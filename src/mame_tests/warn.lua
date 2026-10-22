local frame=0
emu.register_frame_done(function()
  frame=frame+1
  if frame%100==0 then manager.machine.video:snapshot() end
  if frame==1301 then manager.machine:exit() end
end)
