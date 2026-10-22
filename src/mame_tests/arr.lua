local frame=0
local sp=manager.machine.devices[":maincpu"].spaces["program"]
local function pulse(port,n,t) local f=manager.machine.ioport.ports[port].fields[n]; if frame>=t and frame<t+4 then f:set_value(1) elseif frame==t+4 then f:clear_value() end end
emu.register_frame_done(function()
  frame=frame+1
  pulse(":PORT_C","Coin 1",1500)
  for _,t in ipairs({1560,1600,1640,1680}) do pulse(":PORT_D","P1 Down",t) end
  pulse(":PORT_C","1 Player Start",1760)
  pulse(":PORT_C","1 Player Start",1900)
  pulse(":PORT_D","P1 Up",2000)
  pulse(":PORT_C","1 Player Start",2100)
  if frame==1740 or frame==2050 or frame==2300 then manager.machine.video:snapshot(); print(frame,"sel",sp:read_u32(0x0c04f824),"credits",sp:read_u32(0x0c4b75a4)) end
  if frame==1890 or frame==2060 then manager.machine.video:snapshot(); print(frame,"sel",sp:read_u32(0x0c04f824),"credits",sp:read_u32(0x0c4b75a4)) end
  if frame==2301 then manager.machine:exit() end
end)
