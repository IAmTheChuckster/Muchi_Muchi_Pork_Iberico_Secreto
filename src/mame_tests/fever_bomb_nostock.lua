dofile("work/common.lua")
local B=0x0c510b28
local function nb() local n=0; for i=0,1535 do if sp:read_u32(0x0c4c371c+i*92)~=0 then n=n+1 end end; for i=0,255 do local a=0x0c4ec6f8+i*144; local h=sp:read_u32(a+4); if sp:read_u32(a)~=0 and h>=0x0c0d0000 and h<0x0c0e0000 then n=n+1 end end; return n end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame>9150 then sp:write_u8(B+0x214,0) end
  if frame==9095 then sp:write_u32(0x0c04f834,10000) end
  for _,t in ipairs({9100,9200,9260}) do if frame>=t and frame<t+4 then d["P1 Button 3"]:set_value(1) elseif frame==t+4 then d["P1 Button 3"]:clear_value() end end
  if frame>=9195 and frame<9560 and frame%10==0 then print(frame,"b",nb(),"fev",sp:read_u32(0x0c04f838),"cnt",sp:read_u32(0x0c04f834),"req",sp:read_u32(0x0c04f868),"edge",sp:read_u8(0x0c481f3c),"bombs",sp:read_u8(B+0x214),"top",sp:read_u8(B)) end
  if frame==9560 then manager.machine:exit() end
end)
