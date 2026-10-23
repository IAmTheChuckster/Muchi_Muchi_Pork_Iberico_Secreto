dofile("work/common.lua")
local B=0x0c510b28
local P=0x0c52b648
local last={}
local pop,nopop=0,0
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  if frame>3000 then sp:write_u32(0x0c080b30,0x0c0e3110); sp:write_u16(B+0x20e,104) end
  local n=0
  for k=0,199 do local a=P+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then n=n+1; local l=sp:read_u32(a+8); local v=sp:read_u32(a+52)
      if HOLD and last[k] and l==last[k]+1 then if v>=0x20000 and v<0x80000000 then pop=pop+1 else nopop=nopop+1 end end
      last[k]=l else last[k]=nil end end
  if n>0 and frame>7000 and not HOLD then HOLD=frame end
  if HOLD and frame<HOLD+400 then set_nofire(true); d["P1 Button 1"]:clear_value(); if (frame-HOLD)%40<20 then d["P1 Button 2"]:set_value(1) else d["P1 Button 2"]:clear_value() end end
  if HOLD and (frame-HOLD)%50==0 then print(frame-HOLD,"medals",n,"level-ups with pop",pop,"without",nopop) end
  if HOLD and frame==HOLD+400 then manager.machine:exit() end
end)
