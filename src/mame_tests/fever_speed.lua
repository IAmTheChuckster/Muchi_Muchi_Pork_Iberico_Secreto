dofile("work/common.lua")
local B=0x0c510b28
local s0
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  local st=sp:read_u32(0x0c4857c4)
  if frame==8700 then s0=st end
  if frame==8900 then print("normal steps/200 frames",st-s0) end
  if frame==9000 then sp:write_u32(0x0c04f834,10000) end
  if frame>=9100 and frame<9104 then d["P1 Button 3"]:set_value(1) elseif frame==9104 then d["P1 Button 3"]:clear_value() end
  if frame>=9110 and frame<9135 then print("f",frame,"spd",sp:read_u32(0x0c48a168),"acc",sp:read_u32(0x0c04f850),"step",st) end
  if frame==9310 then print("fever steps/200 frames",st-s0,"fev",sp:read_u32(0x0c04f838),"cnt",sp:read_u32(0x0c04f834),"spd",sp:read_u32(0x0c48a168)) end
  if frame==9700 then print("after: fev",sp:read_u32(0x0c04f838),"spd",sp:read_u32(0x0c48a168),"cnt",sp:read_u32(0x0c04f834)) end
  if frame==9136 then manager.machine:exit() end
end)
