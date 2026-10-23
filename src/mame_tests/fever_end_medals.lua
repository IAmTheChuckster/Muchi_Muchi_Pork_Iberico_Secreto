dofile("work/common.lua")
local B=0x0c510b28
local MODE=os.getenv("END") -- "bomb" or "run"
local s0
local function med() local h={}; for k=0,199 do local a=0x0c52b648+k*120; if sp:read_u32(a)~=0 and sp:read_u32(a+4)==5 then local l=sp:read_u32(a+8); h[l]=(h[l] or 0)+1 end end; local t=""; for k,v in pairs(h) do t=t..k..":"..v.." " end; return t end
local function nb() local n=0; for i=0,1535 do if sp:read_u32(0x0c4c371c+i*92)~=0 then n=n+1 end end; return n end
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  for k=1,4 do local t=1520+k*40; if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end
  autoplay(frame)
  sp:write_u8(B+0x203,2)
  if frame==9095 then sp:write_u32(0x0c04f834,10000) end
  if frame>=9100 and frame<9104 then d["P1 Button 3"]:set_value(1) elseif frame==9104 then d["P1 Button 3"]:clear_value() end
  if MODE=="bomb" then if frame>=9400 and frame<9404 then d["P1 Button 3"]:set_value(1) elseif frame==9404 then d["P1 Button 3"]:clear_value() end end
  if MODE=="run" and frame==9399 then sp:write_u32(0x0c04f834,20) end
  local st=sp:read_u32(0x0c4857c4)
  if frame>=9396 and frame<=9412 and frame%2==0 then print(frame,"fev",sp:read_u32(0x0c04f838),"kind",sp:read_u32(0x0c04f88c),"fade",sp:read_u32(0x0c04f878),"bullets",nb(),"medals",med()) end
  if frame==9420 then s0=st end
  if frame>9420 and frame<=9720 and (frame-9420)%60==0 then print(frame,"steps/60f",st-s0,"fade",sp:read_u32(0x0c04f878),"bullets",nb()); s0=st end
  if frame==9721 then manager.machine:exit() end
end)
