# claude-edit-video-resource
Kit để Claude dựng video TikTok 9:16 từ file giọng đọc của kênh **Người Chơi NET**.
Repo gồm: `logo-1.png`, `nhac-nen-short.MP3` (nhạc nền), `engine/` (code), `template.py`, `setup.sh`.

## Quy trình cho Claude (mỗi video = 1 chat mới, tiết kiệm token)
```bash
cd /home/claude && git clone -q https://github.com/chaudev/claude-edit-video-resource kit && cd kit && bash setup.sh
python3 -m engine.asr "/mnt/user-data/uploads/<voice>.mp3" words.json   # in transcript gọn theo đoạn + thời điểm
cp template.py /tmp/v.py   # sửa VOICE, chọn style, viết scenes ngắn gọn, dùng c('cụm từ') để lấy mốc
python3 /tmp/v.py check    # phải chỉ in 'check done' (bắt lỗi đè nhau + ra ngoài lề an toàn)
python3 /tmp/v.py sheet <8-12 mốc> /tmp/s.png   # xem MỘT tấm duy nhất
python3 /tmp/v.py seg 0 25 /tmp/a.mp4 ; seg 25 50 /tmp/b.mp4 ; ...   # ~25s mỗi lệnh (tránh timeout)
python3 /tmp/v.py finish /mnt/user-data/outputs/<ten>.mp4 /tmp/a.mp4 /tmp/b.mp4 ...
```
Tiết kiệm token: không in danh sách từng từ (dùng `Cues`), không đọc lại code engine, chỉ 1 contact sheet, báo cáo ngắn.

## Quy tắc của Chau (cũng nằm trong memory)
- Chữ trên màn hình: cụm ý chính (không phải từ khóa trơn, không phải cả câu). Không phụ đề.
- Hook: tự chọn theo nội dung (số khổng lồ / chữ đập + rung / câu hỏi tò mò...).
- Nhịp đổi cảnh 3 đến 4 giây. Mỗi cảnh một nền động riêng cùng tông style (`assign_variants`).
- Sound effect mức vừa: mỗi nhịp hình chính một tiếng, không dày đặc.
- Render thẳng, không gửi ảnh duyệt trước. Báo cáo sau khi xong: 2 đến 3 câu.
- Nhạc nền repo, giọng +4 dB, nhạc to vừa (mix_audio đã chỉnh sẵn); có sound effect (`engine/sfx.py`, tự tổng hợp).
- Đoạn kêu gọi theo dõi: `logo_cta()` (logo + NGƯỜI CHƠI NET + nút theo dõi).
- Nền luôn chuyển động (mọi style.bg đều động). Mỗi video MỘT style khác video trước.
- Không đè chữ lên nội dung, không sát mép (`check`), thẳng hàng khi so sánh, lưới không lẻ phần tử (số cột chia hết).
- Không phụ đề trừ khi được yêu cầu.

## API nhanh (engine/core.py)
`tx(img,text,font,x,y,color,alpha,scale,dy,group,rot,shadow,anchor)` · `rect` · `chip` · `strike` · `punch` (đập chữ, tự giới hạn trong lề) ·
`counter(t,a,d,v0,v1)` · `ap/pop` (hiện dần / nảy) · `logo_cta` · `Video(scenes, bg_fn, dur, voice, transition, shakes)` · `main(video, SFX)`
Font: `font('bv'|'anton'|'mono'|'hand'|'pixel'|'bungee'|'lora'|'lorai', size, weight)`.
SFX: whoosh whoosh_s whoosh_dn swipe pop pop_hi blip thud impact ding ding_lo power riser scratch, `('typing', gain, dur)` → `(time, name, gain[, dur])`.

## Styles (`engine/styles/*.py`: `VARIANTS`, `bg(t, variant)`, `transition(img,t,dt,variant)`)
- `tech` — tài liệu công nghệ, nền: grid | network | rain | rings | bars; cam/cyan; glitch RGB. Có `sphere`, icon người/thẻ/ngân hàng/ví/tay cầm.
- `poster` — poster cổ động; nền 'pattern/color': rays|stripes|circles|halftone|blocks × red|paper|ink|yel; Anton.
- `blueprint` — bản vẽ kỹ thuật: lưới, la bàn xoay, nét vẽ tự vẽ (`path`, `house`, `dim`, `stampbox`); mono + chữ tay. Nền: grid|iso|graph|plan|protractor × bp|dark.
- `arcade` — game đối kháng; nền: synth | warp | tunnel | tetris | clouds; `hpbar`; VT323 + Bungee; nên dùng `shadow=SHADOW`.
Đã dùng: Garena thẻ cào + Free Fire xấu cố ý (tech) · Free Fire gốc Việt (poster) · Riot/LMHT bị đòi nhà (blueprint) · Free Fire bị Ấn Độ cấm (arcade).
Khi cần style mới: viết module mới trong chat, đưa Chau file để thêm vào repo.
