dofile("work/common.lua")
local S="/tmp/claude-0/-home-claude/07762dfb-baac-5115-bea4-20e9ebaf285a/scratchpad/"
local T={[300]=1,[600]=1,[1650]=1,[3000]=1}
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if T[frame] then local px=manager.machine.screens[":screen"]:pixels(); local f=io.open(S.."s57_"..frame..".raw","wb"); f:write(px); f:close() end
  if frame==3001 then manager.machine:exit() end
end)
