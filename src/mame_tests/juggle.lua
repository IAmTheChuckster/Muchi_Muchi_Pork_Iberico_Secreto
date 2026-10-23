dofile("work/common.lua")
local B=0x0c510b28
local P=0x0c52b648
local function medals() local n,s=0,"" for k=0,199 do local a=P+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then n=n+1; s=s..sp:read_u32(a+8)..string.format("@%d/%d ",sp:read_u32(a+44)>>16,sp:read_u32(a+48)>>16) end end return n,s end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  if frame>3000 then sp:write_u32(0x0c080b30,0x0c0e3110); sp:write_u16(B+0x20e,104) end
  local n,s=medals()
  if n>0 and frame>7000 and not HOLD then HOLD=frame; print("medal appears",frame,s) end
  if HOLD and frame>=HOLD and frame<HOLD+400 then set_nofire(true); d["P1 Button 1"]:clear_value(); d["P1 Button 2"]:set_value(1) end
  if HOLD and frame==HOLD+400 then d["P1 Button 2"]:clear_value() end
  if HOLD and frame>=HOLD and frame<HOLD+400 and (frame-HOLD)%20==0 then print(frame-HOLD,"P",sp:read_u32(B+28)>>16,sp:read_u32(B+32)>>16,"mech",(sp:read_u32(B)>>13)&1,"n",n,s:sub(1,120)) if (frame-HOLD)%60==0 then manager.machine.video:snapshot() end end
  if HOLD and frame==HOLD+401 then manager.machine:exit() end
  if frame>20000 then manager.machine:exit() end
end)
