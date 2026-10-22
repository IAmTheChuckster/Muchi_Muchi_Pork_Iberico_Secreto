local frame=0
emu.register_frame_done(function()
  frame=frame+1
  local c=manager.machine.ioport.ports[":PORT_C"].fields["Coin 1"]
  if frame>=1500 and frame<1504 then c:set_value(1) elseif frame==1504 then c:clear_value() end
  if frame==1300 or frame==1650 then manager.machine.video:snapshot() end
  if frame==1651 then manager.machine:exit() end
end)
