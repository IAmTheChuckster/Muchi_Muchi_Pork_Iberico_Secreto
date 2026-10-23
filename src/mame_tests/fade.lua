dofile("work/common.lua")
local B=0x0c510b28
local S="/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/"
local function nb() local n=0; local c=sp:read_u32(0x0c5108fc); for i=0,c-1 do if sp:read_u32(0x0c4c371c+i*92)~=0 then n=n+1 end end; return n end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame>2000 then sp:write_u8(B+0x203,2) end
  if frame==2700 then sp:write_u32(0x0c04f878,8) end
  if frame>=2694 and frame<=2716 and frame%2==0 then print(frame,"bullets",nb(),"fade",sp:read_u32(0x0c04f878)); local sc=manager.machine.screens[":screen"]; local px=sc:pixels(); local f=io.open(S..string.format("fd%d.raw",frame),"wb"); f:write(px); f:close() end
  if frame==2717 then manager.machine:exit() end
end)
