dofile("work/common.lua")
local B=0x0c510b28
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  if frame>60 then sp:write_u32(0x0c48a164,7) end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame==8000 then sp:write_u32(0x0c04f834,10000); sp:write_u32(0x0c53f4a4,5) end
  for _,t in ipairs({10300,10400}) do if frame>=t and frame<t+4 then d["P1 Button 3"]:set_value(1) elseif frame==t+4 then d["P1 Button 3"]:clear_value() end end
  if frame==10299 or frame==10310 or frame==10500 or frame==10399 or frame==10410 or frame==10600 then print(frame,"cnt",sp:read_u32(0x0c04f834),"fev",sp:read_u32(0x0c04f838),"mode",sp:read_u32(0x0c4eac3c),sp:read_u8(0x0c48227f),sp:read_u8(0x0c516fdc),"chain",sp:read_u32(0x0c53f4a4),"bombs",sp:read_u8(B+0x214),"b217",sp:read_u8(B+0x217),"spd",sp:read_u32(0x0c48a168)) end
  if frame==10711 then manager.machine:exit() end
end)
