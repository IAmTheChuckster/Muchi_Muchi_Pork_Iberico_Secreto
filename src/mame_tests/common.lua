frame = 0
cpu = manager.machine.devices[":maincpu"]
sp = cpu.spaces["program"]
ports = manager.machine.ioport.ports
local P = {}
local function fld(port, name) return manager.machine.ioport.ports[port].fields[name] end
local function pulse(port, name, at, len) if frame>=at and frame<at+len then fld(port,name):set_value(1) elseif frame==at+len then fld(port,name):clear_value() end end
function autoplay(f)
  frame = f
  for _,t in ipairs({1500,2700,3900,5100,6300}) do
    pulse(":PORT_C","Coin 1",t,4)
    pulse(":PORT_C","1 Player Start",t+200,4)
    pulse(":PORT_D","P1 Button 1",t+400,4)
    pulse(":PORT_D","P1 Button 1",t+500,4)
  end
  if sp:read_u8(0x0c510b2b) == 4 and sp:read_u8(0x0c510d2b) < 2 then sp:write_u8(0x0c510d2b, 2) end
  if frame > 6400 then
    local m = frame % 900
    if m < 4 then fld(":PORT_C","Coin 1"):set_value(1) elseif m == 4 then fld(":PORT_C","Coin 1"):clear_value() end
    if m >= 200 and m < 204 then fld(":PORT_C","1 Player Start"):set_value(1) elseif m == 204 then fld(":PORT_C","1 Player Start"):clear_value() end
  end
  if frame > 7200 then
    if not NOFIRE then if frame % 4 < 2 then fld(":PORT_D","P1 Button 1"):set_value(1) else fld(":PORT_D","P1 Button 1"):clear_value() end end
  end
end
function set_nofire(v) NOFIRE = v end
function wiggle(f)
  local ph = (f // 90) % 4
  local P = manager.machine.ioport.ports
  local d = P[":PORT_D"].fields
  for _,n in ipairs({"P1 Left","P1 Right","P1 Up","P1 Down"}) do d[n]:clear_value() end
  if ph == 0 then d["P1 Left"]:set_value(1) elseif ph == 1 then d["P1 Up"]:set_value(1)
  elseif ph == 2 then d["P1 Right"]:set_value(1) else d["P1 Down"]:set_value(1) end
end
