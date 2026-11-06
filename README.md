# Dữ liệu OSM cho Car Launcher SM-T295

Gói dữ liệu đường bộ Bắc Bộ phục vụ đối chiếu GPS và cảnh báo giới hạn tốc độ/lệnh cấm đơn giản. Ứng dụng tải dữ liệu riêng qua HTTPS; APK không đóng gói bản đồ.

© OpenStreetMap contributors. Dữ liệu và cơ sở dữ liệu dẫn xuất được cung cấp theo ODbL 1.0. Xem [NOTICE-OSM.md](NOTICE-OSM.md) và [giấy phép ODbL](https://opendatacommons.org/licenses/odbl/1-0/).

## Gói ban đầu

- Nguồn: [Geofabrik Việt Nam 04/11/2026](https://download.geofabrik.de/asia/vietnam-261104.osm.pbf).
- Vùng: 19,7–24,0°B / 102,0–109,0°Đ, Bắc Bộ và vùng đệm phía Nam.
- 1.323.654 way; 18.340 way có giới hạn tốc độ số theo ít nhất một chiều.
- 14.166.628 đoạn hình học; 791 quan hệ cấm rẽ/hướng bắt buộc được bản hiện tại hỗ trợ.
- SQLite schema 2, manifest format 1; yêu cầu app versionCode 3 trở lên.
- Gói tải ~693,5 MiB, dữ liệu giải nén ~1,67 GiB. Cần dung lượng trống cho cả gói mới và gói đang dùng khi cập nhật.

Tải gói ở mục Releases, không lấy tệp lớn bằng Git clone. URL manifest thô cho app là:

`https://raw.githubusercontent.com/baokhanh225/car-launcher-data/main/manifest.json`

## Phạm vi và giới hạn

Đây không phải danh sách đầy đủ mọi biển báo vật lý. OSM có thể thiếu/cũ dữ liệu. Không suy tốc độ pháp định từ loại đường hoặc tốc độ xe. Các hạn chế theo giờ/làn/via-way và tình huống chưa hiểu không được trình bày như lệnh cấm cố định. Luôn đối chiếu biển thực tế.

Nguồn này độc lập RORE và Google Maps. Không chứa code/tài nguyên/cơ chế cấp phép RORE hoặc dữ liệu Google Maps.

## Tạo bản mới

Công cụ `tools/build_north.py` và `tools/pack_data.py` tái tạo SQLite/gzip từ trích xuất Geofabrik. Mỗi bản dùng tag release mới và version manifest tăng dần. Tải gói đầy đủ lên release trước, cập nhật manifest cuối cùng. App chỉ kiểm tra theo lịch trên Wi-Fi; nguồn này không cam kết phát hành dữ liệu mới hằng ngày.
