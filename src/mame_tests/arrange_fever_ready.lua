dofile("work/common.lua")
local S="/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/"
local function row34() local s=""; for r=0,13 do local v=sp:read_u32(0x0c483a50+(34*30+r)*4); local c=v&0xff; s=s..((c>=32 and c<127) and string.char(c) or ".") end; return s end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u32(0x0c04f86c,50)
  if frame>=3000 and frame<3100 then sp:write_u32(0x0c04f834,(frame<3020) and 5000 or 10000) end
  if frame>=3000 and frame<3100 and frame%6==0 then print("F",frame,"cnt",sp:read_u32(0x0c04f834),"[",row34(),"]",string.format("%08x",sp:read_u32(0x0c483a50+(34*30)*4))) end
  if frame==3050 or frame==3066 then local px=manager.machine.screens[":screen"]:pixels(); local f=io.open(S.."ready"..frame..".raw","wb"); f:write(px); f:close() end
  if frame==3100 then manager.machine:exit() end
end)
