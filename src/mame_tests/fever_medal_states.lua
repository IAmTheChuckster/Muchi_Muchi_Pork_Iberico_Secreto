dofile("work/common.lua")
local B=0x0c510b28
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  if frame>9000 and frame<9160 then manager.machine.ioport.ports[':PORT_D'].fields['P1 Up']:set_value(1) end
  if frame==9095 then sp:write_u32(0x0c04f834,10000) end
  if frame>=9100 and frame<9104 then d["P1 Button 3"]:set_value(1) elseif frame==9104 then d["P1 Button 3"]:clear_value() end
  if frame>=9100 and frame<9160 and frame%4==1 then local h={}; local n=0
    for k=0,199 do local a=0x0c52b648+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then n=n+1; local st=sp:read_u8(a+116); h[st]=(h[st] or 0)+1 end end
    local s=""; for k,v in pairs(h) do s=s..k..":"..v.." " end; local py,px=sp:read_u32(B+28)>>16,sp:read_u32(B+32)>>16; local dsum=0; local vs=""; local c=0; for k=0,199 do local a=0x0c52b648+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then local y=sp:read_u32(a+44)>>16; local x=sp:read_u32(a+48)>>16; dsum=dsum+math.abs(y-py)+math.abs(x-px); if c<3 then vs=vs..string.format("[%d,%d v%08x/%08x] ",y,x,sp:read_u32(a+52),sp:read_u32(a+56)) end; c=c+1 end end; s=s.." avgdist "..(c>0 and dsum//c or 0).." "..vs
    print(frame,"medals",n,"states",s,"player",sp:read_u32(B+28)>>16,sp:read_u32(B+32)>>16) end
  if frame==9160 then manager.machine:exit() end
end)
