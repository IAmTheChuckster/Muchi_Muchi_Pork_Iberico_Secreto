dofile("work/common.lua")
local B=0x0c510b28
local lf,lt=-1,-1
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame>=7000 and frame<7010 then sp:write_u32(0x0c04f834,10000) end
  local f=sp:read_u32(0x0c04f838); local t=sp:read_u8(B)
  if frame>7000 and (f~=lf or t~=lt) then print(frame,"fev",f,"top",string.format("%02x",t),"cnt",sp:read_u32(0x0c04f834),"lives",sp:read_u8(B+0x203),"grace",sp:read_u32(0x0c04f86c)); lf=f; lt=t end
  if frame==9000 then manager.machine:exit() end
end)
