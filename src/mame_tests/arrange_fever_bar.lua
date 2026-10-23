dofile("work/common.lua")
local S="/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/"
local vals={0,2500,5000,9999,10000}
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u32(0x0c04f86c,50)
  if frame>=3000 and frame<3050 then local k=(frame-3000)//10+1; sp:write_u32(0x0c04f834,vals[k]); if (frame-3000)%10==9 then local s=""; for r=0,7 do s=s..string.format("%08x ",sp:read_u32(0x0c483a50+(35*30+r)*4)) end; print("V",vals[k],s) end end
  if frame==3060 then sp:write_u32(0x0c04f834,10000) end
  if frame>=3100 and frame<3104 then d["P1 Button 3"]:set_value(1) elseif frame==3104 then d["P1 Button 3"]:clear_value() end
  if frame==3300 then local s=""; for r=0,7 do s=s..string.format("%08x ",sp:read_u32(0x0c483a50+(35*30+r)*4)) end; print("FEVER cnt",sp:read_u32(0x0c04f834),"fev",sp:read_u32(0x0c04f838),s)
    local px=manager.machine.screens[":screen"]:pixels(); local f=io.open(S.."bar54.raw","wb"); f:write(px); f:close(); manager.machine:exit() end
end)
