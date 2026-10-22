dofile("src/mame_tests/common.lua")
local H={[0x0c0af9c0]="S3mid",[0x0c0b2f70]="S4midA",[0x0c0b4b50]="S4midB",[0x0c0b8050]="S5midA",[0x0c0b6890]="S5midB"}
local function line(col) local s=""; for r=12,16 do local c=sp:read_u32(0x0c483a50+(col*30+r)*4)&0xff; s=s..((c>=32 and c<127) and string.char(c) or " ") end; return s end
local shown={}; local pauseAt=nil; local last=""
emu.register_frame_done(function()
  frame = frame + 1
  autoplay(frame)
  local cur=nil
  for s=0,191 do local b=0x0c4b7c9c+s*200; local nm=H[sp:read_u32(b+4)]; if nm and sp:read_u32(b)~=0 and sp:read_u8(b+0x0f)==0 then cur=nm end end
  local t=line(36)
  if cur and t~="     " and not shown[cur] then shown[cur]=frame; print("timer-start", cur, frame, "["..t.."]") end
  if cur and shown[cur] and (frame-shown[cur])%600==0 and frame>shown[cur] then print("  ", cur, "+"..(frame-shown[cur]), "["..t.."]") end
  if cur=="S5midB" and shown.S5midB and not pauseAt and frame==shown.S5midB+120 then pauseAt=frame end
  if pauseAt and frame>=pauseAt and frame<pauseAt+300 then sp:write_u8(0x0c51091c,1) end
  if pauseAt and (frame==pauseAt-1 or frame==pauseAt+100 or frame==pauseAt+200 or frame==pauseAt+299) then
    print("PAUSED", frame-pauseAt, "timer["..t.."]", "gfc", sp:read_u32(0x0c516fd0), "step", sp:read_u32(0x0c4857c4)) end
  if pauseAt and frame==pauseAt+310 then manager.machine:exit() end
  if frame==130000 then manager.machine:exit() end
end)
