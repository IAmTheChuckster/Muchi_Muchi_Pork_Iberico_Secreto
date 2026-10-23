dofile("work/common.lua")
local B=0x0c510b28
local s0,lastst,lastfev=0,0,-1
local function nb() local n=0; local c=sp:read_u32(0x0c5108fc); for i=0,c-1 do if sp:read_u32(0x0c4c371c+i*92)~=0 then n=n+1 end end; return n end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame%1500==0 and frame>=7500 then sp:write_u32(0x0c04f834,10000) end
  local m=frame%1500
  if frame>7500 and m>=100 and m<104 then d["P1 Button 3"]:set_value(1) elseif m==104 then d["P1 Button 3"]:clear_value() end
  local st=sp:read_u32(0x0c4857c4)
  local fev=sp:read_u32(0x0c04f838)
  local top=sp:read_u8(B)
  if fev~=lastfev or top~=lastst then print(frame,"fev",fev,"top",string.format("%02x",top),"cnt",sp:read_u32(0x0c04f834),"chain",sp:read_u32(0x0c53f4a4),"grace",sp:read_u32(0x0c04f86c),"mode",sp:read_u8(0x0c516fdc)); lastfev=fev; lastst=top end
  if frame%30==0 then local ds=st-s0; s0=st; if fev==1 or frame%300==0 then print(frame,"steps/30f",ds,"bullets",nb(),"fev",fev) end end
  if frame==12100 then manager.machine:exit() end
end)
