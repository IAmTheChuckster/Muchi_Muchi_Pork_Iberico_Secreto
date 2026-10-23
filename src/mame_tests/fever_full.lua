dofile("work/common.lua")
local B=0x0c510b28
local P=0x0c52b648
local function medals() local n,s=0,"" for k=0,199 do local a=P+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then n=n+1; s=s..sp:read_u32(a+8).."," end end return n,s end
local s0
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  if frame>60 then sp:write_u32(0x0c48a164,7) end
  autoplay(frame)
  if frame>3000 then sp:write_u32(0x0c080b30,0x0c0e3110) end
  if frame==8000 then sp:write_u32(0x0c04f834,10000); sp:write_u32(0x0c53f4a4,5) end
  if frame>=8000 and frame<9000 and frame%100==0 then local n,s=medals(); print(frame,"full: cnt",sp:read_u32(0x0c04f834),"medals",n,s:sub(1,60)) end
  if frame>=9000 and frame<9004 then d["P1 Button 3"]:set_value(1) elseif frame==9004 then d["P1 Button 3"]:clear_value() end
  local st=sp:read_u32(0x0c4857c4)
  if frame==9010 then s0=st end
  if frame==9210 then print("fever steps per 200 frames",st-s0) end
  if frame>9000 and frame%300==0 then print(frame,"cnt",sp:read_u32(0x0c04f834),"fev",sp:read_u32(0x0c04f838),"chain",sp:read_u32(0x0c53f4a4),"spd",sp:read_u32(0x0c48a168)) end
  if frame==13000 then manager.machine:exit() end
end)
