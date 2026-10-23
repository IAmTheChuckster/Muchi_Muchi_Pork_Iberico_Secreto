dofile("work/common.lua")
local B=0x0c510b28
local function nb() local n=0; local c=sp:read_u32(0x0c5108fc); for i=0,c-1 do if sp:read_u32(0x0c4c371c+i*92)~=0 then n=n+1 end end; return n end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame==8500 then sp:write_u32(0x0c04f834,10000) end
  if frame>=9100 and frame<9104 then d["P1 Button 3"]:set_value(1) elseif frame==9104 then d["P1 Button 3"]:clear_value() end
  if (frame>=9096 and frame<9260) or (frame>=9384 and frame<9560) then local m=0; for k=0,199 do local a=0x0c52b648+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then m=m+1 end end; print(frame,"fev",sp:read_u32(0x0c04f838),"bullets",nb(),"medals",m,"cnt5108fc",sp:read_u32(0x0c5108fc)) end
  if frame==9560 then manager.machine:exit() end
end)
