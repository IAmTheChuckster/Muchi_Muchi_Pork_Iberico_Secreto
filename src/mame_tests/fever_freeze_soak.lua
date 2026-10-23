dofile("work/common.lua")
local B=0x0c510b28
local last,still=0,0
local fv=0
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  if frame>3000 then
    if sp:read_u32(0x0c04f838)==1 then fv=fv+1; if sp:read_u32(0x0c04f834)<3000 then sp:write_u32(0x0c04f834,9000) end
    elseif frame%400==0 then sp:write_u32(0x0c04f834,10000); sp:write_u32(0x0c04f868,1) end
    sp:write_u16(B+0x20e,104); local m=frame%300; if m<220 then set_nofire(true); d["P1 Button 1"]:clear_value(); d["P1 Button 2"]:set_value(1) else set_nofire(false); d["P1 Button 2"]:clear_value() end end
  local st=sp:read_u32(0x0c4857c4)
  if st==last then still=still+1 else still=0 end
  last=st
  if frame>3000 and still==300 then print("FROZEN at",frame,string.format("pc=%08x",manager.machine.devices[":maincpu"].state["PC"].value),"fev",sp:read_u32(0x0c04f838)); manager.machine:exit() end
  if frame%5000==0 then local n=0; for k=0,199 do local a=0x0c52b648+k*120; if sp:read_u32(a)~=0 then n=n+1 end end; print(frame,"fever frames so far",fv,"items",n) end
  if frame==36000 then local f=io.open("/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/ramcode.bin","wb"); for i=0,6283,4 do local v=sp:read_u32(0x0c04c000+i); f:write(string.pack(">I4",v)) end; f:close(); print("no freeze"); manager.machine:exit() end
end)
