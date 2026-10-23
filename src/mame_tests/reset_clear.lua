dofile("work/common.lua")
local function fld(p,n) return manager.machine.ioport.ports[p].fields[n] end
local function pulse(p,n,at,len) if frame>=at and frame<at+len then fld(p,n):set_value(1) elseif frame==at+len then fld(p,n):clear_value() end end
local done=false
emu.register_frame_done(function()
  frame=frame+1
  pulse(":PORT_C","Coin 1",1500,4); pulse(":PORT_C","1 Player Start",1700,4)
  for k=1,4 do pulse(":PORT_D","P1 Down",1520+k*40,4) end
  pulse(":PORT_D","P1 Button 1",1880,4)
  if frame==2400 then sp:write_u32(0x0c04f834,10000); sp:write_u32(0x0c04fa10,1234) end
  if frame==2600 and not done then done=true; print("before reset","cnt",sp:read_u32(0x0c04f834),"arr",sp:read_u32(0x0c04f830),"act",sp:read_u32(0x0c04f884),"cd",sp:read_u32(0x0c04fa10)); manager.machine:soft_reset() end
end)
emu.register_start(function() if done then end end)
local f2=0
emu.register_frame_done(function() if done then f2=f2+1; if f2==300 then print("after reset","cnt",sp:read_u32(0x0c04f834),"arr",sp:read_u32(0x0c04f830),"act",sp:read_u32(0x0c04f884),"cd",sp:read_u32(0x0c04fa10)); manager.machine:exit() end end end)
