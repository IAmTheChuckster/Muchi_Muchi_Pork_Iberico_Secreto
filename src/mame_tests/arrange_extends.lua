dofile("work/common.lua")
local B=0x0c510b28
local l,lv=-1,-1
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  if frame==3000 then sp:write_u8(B+0x203,2) end
  if frame==5000 then sp:write_u32(B+0x228,29990000) end
  if frame==7000 then sp:write_u32(B+0x228,59995000) end
  local th=sp:read_u32(B+0x22c); local lives=sp:read_u8(B+0x203)
  if frame>2900 and (th~=l or lives~=lv) then print(frame,"score",sp:read_u32(B+0x228),"next",th,"lives",lives); l=th; lv=lives end
  if frame==9000 then manager.machine:exit() end
end)
