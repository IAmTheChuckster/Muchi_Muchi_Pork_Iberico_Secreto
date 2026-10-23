dofile("work/common.lua")
local B=0x0c510b28
local function fld(p,n) return manager.machine.ioport.ports[p].fields[n] end
local function pulse(p,n,at,len) if frame>=at and frame<at+len then fld(p,n):set_value(1) elseif frame==at+len then fld(p,n):clear_value() end end
local last=""
emu.register_frame_done(function()
  frame=frame+1
  pulse(":PORT_C","Coin 1",1500,4); pulse(":PORT_C","1 Player Start",1700,4)
  for k=1,4 do pulse(":PORT_D","P1 Down",1520+k*40,4) end
  pulse(":PORT_D","P1 Right",1800,4); pulse(":PORT_D","P1 Right",1830,4)
  pulse(":PORT_D","P1 Button 1",1880,4)
  local s=string.format("top=%02x step=%d arr=%d fs=%02x pend=%d bombs=%d next=%d",sp:read_u8(B),sp:read_u32(0x0c4857c4)%100000,sp:read_u32(0x0c04f830),sp:read_u8(0x0c04f844),sp:read_u8(0x0c04f846),sp:read_u8(B+0x214),sp:read_u32(B+0x22c))
  local k=s:gsub("step=%d+ ","")
  if k~=last then print(frame,s); last=k end
  if frame==2300 then manager.machine:exit() end
end)
