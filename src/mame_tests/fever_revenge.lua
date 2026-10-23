dofile("work/common.lua")
local B=0x0c510b28
local dbg
local function count() local n=0; for _,l in ipairs(dbg.consolelog) do if l:find("REV") then n=n+1 end end; return n end
local c0=0
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  if frame==10 then dbg=manager.machine.debugger; dbg:command('bpset 0c0d7510,1,{printf "REV"; g}'); dbg:command("go") end
  if frame==9095 then sp:write_u32(0x0c04f834,10000) end
  if frame>=9100 and frame<9104 then d["P1 Button 3"]:set_value(1) elseif frame==9104 then d["P1 Button 3"]:clear_value() end
  if frame%300==0 and frame>=8400 then local c=count(); print(frame,"fev",sp:read_u32(0x0c04f838),"rvflag",sp:read_u32(0x0c04f888),"revenge calls in last 300f",c-c0); c0=c end
  if frame==10200 then manager.machine:exit() end
end)
