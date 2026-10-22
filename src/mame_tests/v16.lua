dofile("src/mame_tests/common.lua")
local V = os.getenv("V101") == "1"
local B=0x0c510b28
local t0=nil
local last, lastp = "", ""
emu.register_frame_done(function()
  frame=frame+1
  local d=manager.machine.ioport.ports[":PORT_D"].fields
  if V then for _,t in ipairs({1560,1600,1640}) do if frame>=t and frame<t+4 then d["P1 Down"]:set_value(1) elseif frame==t+4 then d["P1 Down"]:clear_value() end end end
  if not t0 then
    autoplay(frame)
    local p=string.format("pow=%d cnt=%d bomb=%d bgauge=%d lives=%d", sp:read_u8(B+0x20b),sp:read_u8(B+0x20c),sp:read_u8(B+0x214),sp:read_u8(B+0x215),sp:read_u8(B+0x203))
    if p~=lastp then print(frame,"ITEM",p); lastp=p end
    if frame%500==0 then print(frame,"ST",string.format("%08x 21a=%d 21b=%d pow=%d",sp:read_u32(B),sp:read_u8(B+0x21a),sp:read_u8(B+0x21b),sp:read_u8(B+0x20b))) end
    local st=sp:read_u32(0x0c4857c4); local adv=(st~=(LASTST or -1)); LASTST=st
    if frame>9000 and adv and frame%900>220 and frame%900<300 and sp:read_u8(B+0x20b)>=1 and (sp:read_u32(B)>>24)==0xce then t0=frame; set_nofire(true); fld=nil; d["P1 Button 1"]:clear_value(); print("T0",t0) end
    if frame>20000 then manager.machine:exit() end
    return
  end
  local f=frame-t0
  if sp:read_u8(B+0x203)<2 then sp:write_u8(B+0x203,2) end
  if f==1 then sp:write_u16(B+0x20e,52) end
  local b=(f>=30 and f<90) or (f>=150 and f<180) or (f>=240 and f<245)
  if b then d["P1 Button 2"]:set_value(1) else d["P1 Button 2"]:clear_value() end
  d["P1 Button 1"]:clear_value()
  local s=string.format("in=%02x pz=%d B=%d mech=%d lard=%d 20a=%d tm=%d 212=%d 21a=%d/%d pow=%d step=%d", sp:read_u8(B+0x1f8), sp:read_u8(0x0c51091c), b and 1 or 0, (sp:read_u32(B)>>13)&1, sp:read_u16(B+0x20e), sp:read_u8(B+0x20a), sp:read_u16(B+0x210), sp:read_u16(B+0x212), sp:read_u8(B+0x21a), sp:read_u8(B+0x21b), sp:read_u8(B+0x20b), sp:read_u32(0x0c4857c4)//50)
  if s~=last then print(f,s); last=s end
  if f>=30 and f<=78 and f%4==2 then manager.machine.video:snapshot(); print("SNAP",f) end
  if f==320 then manager.machine:exit() end
end)
