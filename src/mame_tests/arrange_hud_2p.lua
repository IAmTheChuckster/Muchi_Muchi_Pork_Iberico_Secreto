dofile("work/common.lua")
local B2=0x0c510d28
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  local c=manager.machine.ioport.ports[":PORT_C"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame==2600 then sp:write_u32(0x0c04f834,1234) end
  if frame>=2700 and frame<2704 then c["Coin 1"]:set_value(1) elseif frame==2704 then c["Coin 1"]:clear_value() end
  if frame>=2800 and frame<2804 then c["2 Players Start"]:set_value(1) elseif frame==2804 then c["2 Players Start"]:clear_value() end
  if frame==3300 then
    for col=35,39 do local s=""; for row=0,29 do local v=sp:read_u32(0x0c483a50+(col*30+row)*4); local ch=v&0xff; s=s..((ch>=32 and ch<127) and string.char(ch) or ".") end; print("COL",col,s) end
    print("P2 state",string.format("%02x",sp:read_u8(B2)))
    local px=manager.machine.screens[":screen"]:pixels(); local f=io.open("/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/hud53.raw","wb"); f:write(px); f:close()
    manager.machine:exit() end
end)
