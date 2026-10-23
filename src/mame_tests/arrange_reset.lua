dofile("work/common.lua")
local B=0x0c510b28
local function fld(p,n) return manager.machine.ioport.ports[p].fields[n] end
local function pulse(p,n,at,len) if frame>=at and frame<at+len then fld(p,n):set_value(1) elseif frame==at+len then fld(p,n):clear_value() end end
local NEW=tonumber(os.getenv("NEW") or "6000")
emu.register_frame_done(function()
  frame=frame+1
  -- first game: coin, start, ARRANGE+, go
  pulse(":PORT_C","Coin 1",1500,4); pulse(":PORT_C","1 Player Start",1700,4)
  for k=1,4 do pulse(":PORT_D","P1 Down",1520+k*40,4) end
  pulse(":PORT_D","P1 Button 1",1900,4); pulse(":PORT_D","P1 Button 1",2000,4)
  if frame==2500 then sp:write_u32(0x0c04f834,1799); sp:write_u8(B+0x203,0) end
  -- second game (new game from the title) or continue
  pulse(":PORT_C","Coin 1",NEW,4); pulse(":PORT_C","1 Player Start",NEW+200,4)
  for k=1,4 do pulse(":PORT_D","P1 Down",NEW+220+k*40,4) end
  pulse(":PORT_D","P1 Button 1",NEW+400,4); pulse(":PORT_D","P1 Button 1",NEW+500,4)
  if frame%250==0 then print(frame,"cnt",sp:read_u32(0x0c04f834),"lives",sp:read_u8(B+0x203),"top",string.format("%02x",sp:read_u8(B)),"arr",sp:read_u32(0x0c04f830)) end
  if frame==NEW+1500 then manager.machine:exit() end
end)
