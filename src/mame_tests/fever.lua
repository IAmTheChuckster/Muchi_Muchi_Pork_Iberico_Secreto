dofile("work/common.lua")
local B=0x0c510b28
local P=0x0c52b648
local function medals() local n,s=0,"" for k=0,199 do local a=P+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then n=n+1; s=s..sp:read_u32(a+8).."," end end return n,s end
local function bullets() local n=0 for k=0,383 do if sp:read_u32(0x0c4c371c+k*92)~=0 then n=n+1 end end return n end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if sp:read_u8(B+0x203)<2 then sp:write_u8(B+0x203,2) end
  -- juggling test: restore 40-kill medal list so medals appear, keep lard full, hold B from 7000-8500
  if frame>3000 and frame<8500 then sp:write_u32(0x0c080b30,0x0c0e3110); sp:write_u16(B+0x20e,104) end
  if frame>=7000 and frame<8500 then set_nofire(true); d["P1 Button 1"]:clear_value(); d["P1 Button 2"]:set_value(1)
    for k=0,199 do local a=P+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 and sp:read_u32(a+8)<18 then sp:write_u32(a+44,sp:read_u32(B+28)+0x500000); sp:write_u32(a+48,sp:read_u32(B+32)) end end
  elseif frame==8500 then d["P1 Button 2"]:clear_value(); set_nofire(false) end
  if frame==9000 then sp:write_u32(0x0c04f834,10000) end
  if frame>=9100 and frame<9104 then d["P1 Button 3"]:set_value(1) elseif frame==9104 then d["P1 Button 3"]:clear_value() end
  if frame%100==0 and frame>=6900 or (frame>=9098 and frame<=9110) then
    local n,s=medals()
    print(frame,"cnt",sp:read_u32(0x0c04f834),"fev",sp:read_u32(0x0c04f838),"medals",n,"bul",bullets(),"bombs",sp:read_u8(B+0x214),"mech",(sp:read_u32(B)>>13)&1,"lv",s:sub(1,80))
  end
  if frame==9102 or frame==9106 or frame==8000 then manager.machine.video:snapshot() end
  if frame==10200 then manager.machine:exit() end
end)
