dofile("work/common.lua")
local DOWNS=tonumber(os.getenv("DOWNS") or "4")
local dbg
local function fld(p,n) return manager.machine.ioport.ports[p].fields[n] end
local function pulse(p,n,at,len) if frame>=at and frame<at+len then fld(p,n):set_value(1) elseif frame==at+len then fld(p,n):clear_value() end end
emu.register_frame_done(function()
  frame=frame+1
  pulse(":PORT_C","Coin 1",1500,4); pulse(":PORT_C","1 Player Start",1700,4)
  for k=1,DOWNS do pulse(":PORT_D","P1 Down",1520+k*40,4) end
  pulse(":PORT_D","P1 Right",1800,4); pulse(":PORT_D","P1 Right",1830,4)
  pulse(":PORT_D","P1 Button 1",1880,4)
  if frame==2300 then manager.machine:exit() end
end)
