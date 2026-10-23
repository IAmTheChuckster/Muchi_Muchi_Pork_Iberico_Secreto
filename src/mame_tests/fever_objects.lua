dofile("work/common.lua")
local B=0x0c510b28
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame==8500 then sp:write_u32(0x0c04f834,10000) end
  if frame==9098 then
    local t={}; for k=0,199 do local a=0x0c52b648+k*120; if sp:read_u32(a)~=0 then local ty=sp:read_u32(a+4); t[ty]=(t[ty] or 0)+1 end end
    for k,v in pairs(t) do print("itemtype",k,v) end
    print("player",sp:read_u32(B+28)>>16,sp:read_u32(B+32)>>16)
    local n=0; for i=0,383 do local a=0x0c4c371c+i*92; if sp:read_u32(a)~=0 and n<8 then n=n+1; print("bul",i,sp:read_u32(a+32)>>16,sp:read_u32(a+36)>>16,string.format("%08x %08x",sp:read_u32(a+4),sp:read_u32(a+48))) end end
    manager.machine:exit() end
end)
