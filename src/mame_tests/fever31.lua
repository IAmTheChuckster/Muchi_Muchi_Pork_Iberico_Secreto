dofile("work/common.lua")
local B=0x0c510b28
local P=0x0c52b648
local lastfev,lastmpk=-1,-1
local function nb() local n=0; local c=sp:read_u32(0x0c5108fc); for i=0,c-1 do if sp:read_u32(0x0c4c371c+i*92)~=0 then n=n+1 end end; return n end
local function med() local n,up=0,0; for k=0,199 do local a=P+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then n=n+1; local v=sp:read_u32(a+52); if v<0x80000000 and v>=0x20000 then up=up+1 end end end; return n,up end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame==8500 or frame==10400 then sp:write_u32(0x0c04f834,10000) end
  for _,t in ipairs({9100,10600}) do if frame>=t and frame<t+4 then d["P1 Button 3"]:set_value(1) elseif frame==t+4 then d["P1 Button 3"]:clear_value() end end
  local fev=sp:read_u32(0x0c04f838); local mp=sp:read_u8(0x0c516fdc)
  if fev~=lastfev or mp~=lastmpk then print(frame,"fev",fev,"mode",mp,"cnt",sp:read_u32(0x0c04f834),"bullets",nb(),"fade",sp:read_u32(0x0c04f878),"grace",sp:read_u32(0x0c04f86c),"top",sp:read_u8(B)); lastfev=fev; lastmpk=mp end
  if (frame>=9100 and frame<9140) and frame%6==0 then local n,u=med(); print(frame,"medals",n,"rising",u) end
  if fev==0 and lastend and frame-lastend<20 and frame%2==0 then print(frame,"after end bullets",nb(),"fade",sp:read_u32(0x0c04f878)) end
  if fev==1 then fevon=true elseif fevon then fevon=false; lastend=frame end
  if frame==9112 or frame==9387 or frame==9389 or frame==9391 or frame==9393 then local sc=manager.machine.screens[":screen"]; local px,w,h=sc:pixels(); local f=io.open(string.format("/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/px%d_%dx%d.raw",frame,w,h),"wb"); f:write(px); f:close() end
  if frame==11600 then manager.machine:exit() end
end)
