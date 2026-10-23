dofile("work/common.lua")
local B=0x0c510b28
local S="/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/"
local FULL=os.getenv("FULL")=="1"
local function nb() local n,m=0,0; for i=0,1535 do local a=0x0c4c371c+i*92; if sp:read_u32(a)~=0 then n=n+1; if sp:read_u32(a+64)~=0 then m=m+1 end end end; return n,m end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if FULL and frame>=4000 and frame<4600 then sp:write_u32(0x0c04f834,10000); sp:write_u32(0x0c04f86c,50) end
  if frame>=3900 and frame<=4600 and frame%50==0 then local n,m=nb(); print(frame,"bullets",n,"marked",m,"act",sp:read_u32(0x0c04f884),"fev",sp:read_u32(0x0c04f838),"mode",sp:read_u8(0x0c516fdc)) end
  if frame==4400 then local px=manager.machine.screens[":screen"]:pixels(); local f=io.open(S..(FULL and "dblon.raw" or "dbloff.raw"),"wb"); f:write(px); f:close() end
  if frame==4601 then manager.machine:exit() end
end)
