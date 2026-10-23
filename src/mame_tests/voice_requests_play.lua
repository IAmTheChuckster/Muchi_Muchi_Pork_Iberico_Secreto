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
  if frame>2100 then autoplay(frame) end
  if frame>2000 then sp:write_u8(0x0c510b28+0x203,2) end
  if frame==10 then dbg=manager.machine.debugger
    dbg:command('bpset 0c088bc0,1,{printf "V REQ r4=%x r5=%x",r4,r5; g}')
    dbg:command('bpset 0c088bea,1,{printf "V QUEUED r5=%x",r5; g}')
    dbg:command('bpset 0c088c10,1,{printf "V NOW r3=%x",r3; g}')
    dbg:command("go") end
  if frame==9000 then local h={}; for _,l in ipairs(dbg.consolelog) do if l:find("^V ") then h[l]=(h[l] or 0)+1 end end
    for k,v in pairs(h) do print("C",v,k) end; print("char", sp:read_u8(0x0c510b28+0x201), sp:read_u8(0x0c510b28+0x202)); manager.machine:exit() end
end)
