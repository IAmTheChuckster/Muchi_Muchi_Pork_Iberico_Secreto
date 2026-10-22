dofile("src/mame_tests/common.lua")
local last=""
local function line(col) local s=""; for r=10,19 do local c=sp:read_u32(0x0c483a50+(col*30+r)*4)&0xff; s=s..((c>=32 and c<127) and string.char(c) or " ") end; return s end
local snapAt={}
emu.register_frame_done(function()
  frame = frame + 1
  local d = manager.machine.ioport.ports[":PORT_D"].fields
  for _,t in ipairs({1560,1600,1640}) do if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  local loop=sp:read_u32(0x0c48201c); local idx=sp:read_u32(0x0c04f82c); local flag=sp:read_u32(0x0c04f828)
  local mode=sp:read_u32(0x0c4eac3c); local m2=sp:read_u8(0x0c48227f); local m3=sp:read_u8(0x0c516fdc)
  local key=string.format("loop=%d idx=%d flag=%d mode=%d/%d/%d", loop, idx, flag, mode, m2, m3)
  if key~=last then print(frame, key, "c37["..line(37).."]", "score", sp:read_u32(0x0c510b28+0x228)); last=key; snapAt[frame+300]=true end
  if snapAt[frame] then manager.machine.video:snapshot(); print("SNAP", frame) end
  if frame%20000==0 then print(frame, "tick", key, "c37["..line(37).."] c36["..line(36).."] c35["..line(35).."]", "lives", sp:read_u8(0x0c510d2b)) end
  if frame==480000 then manager.machine:exit() end
end)
