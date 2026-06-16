def generate_interpretation(test_name, result_value, reference_range=None, flag=None):

    name = (test_name or "").lower()
    value_text = str(result_value or "").strip()

    try:
        value = float(value_text)
    except:
        value = None

    if "hba1c" in name:
        if value is not None and value >= 6.5:
            return "HbA1c cao hon nguong tham chieu. Ket qua goi y kiem soat duong huyet chua toi uu, co the phu hop voi nguy co dai thao duong. Khuyen nghi benh nhan tham khao bac si chuyen khoa."
        if value is not None and value >= 5.7:
            return "HbA1c nằm trong vùng tăng nhẹ. Kết quả có thể gợi ý nguy cơ tiền dai thao duong. Nên theo dõi duong huyet và điều chỉnh lối sống."
        return "HbA1c trong khoảng tham chiếu. Tiếp tục duy trì chế độ sinh hoạt lành mạnh."

    if "glucose" in name or "đường" in name:
        if value is not None and value > 126:
            return "Glucose máu tăng. Cần đánh giá thêm theo bối cảnh lâm sàng và thời điểm lấy mẫu."
        return "Glucose không ghi nhận bất thường rõ dựa trên dữ liệu hiện có."

    if "cholesterol" in name:
        if value is not None and value > 200:
            return "Cholesterol tăng. Có thể liên quan nguy cơ tim mạch, nên tư vấn bac si để đánh giá thêm."
        return "Cholesterol trong giới hạn chấp nhận được theo dữ liệu hiện có."

    if "triglyceride" in name:
        if value is not None and value > 150:
            return "Triglyceride tăng. Nên kiểm soát chế độ ăn, cân nặng và đánh giá nguy cơ chuyển hóa."
        return "Triglyceride không ghi nhận bất thường rõ."

    if "alt" in name or "ast" in name:
        if value is not None and value > 40:
            return "Men gan tăng. Cần xem xét thêm tiền sử dùng thuốc, rượu bia, viêm gan hoặc bệnh lý gan mật."
        return "Men gan trong khoảng tham chiếu."

    if "creatinine" in name:
        if value is not None and value > 1.3:
            return "Creatinine tăng. Có thể gợi ý giảm chức năng thận, cần đánh giá thêm eGFR và tình trạng lâm sàng."
        return "Creatinine không ghi nhận bất thường rõ."

    if "cbc" in name or "complete blood count" in name:
        return "Cong thuc mau can duoc dien giai theo tung chi so thanh phan nhu WBC, RBC, Hb, Hct va tieu cau."

    if flag == "HIGH":
        return "Kết quả cao hơn khoảng tham chiếu. Cần bac si đánh giá theo triệu chứng và tiền sử bệnh."
    
    if flag == "LOW":
        return "Kết quả thấp hơn khoảng tham chiếu. Cần bac si đánh giá theo bối cảnh lâm sàng."

    return "Chưa có rule diễn giải tự động cho xét nghiệm này. Cần bac si hoặc kỹ thuật viên xem xét."

def interpret_result(test_name, result_value, reference_range=None, flag=None):
    return generate_interpretation(
        test_name,
        result_value,
        reference_range,
        flag
    )
