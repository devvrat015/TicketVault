from io import BytesIO

import qrcode

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def generate_ticket_pdf(booking, seat, event) -> bytes:
    buffer = BytesIO()

    # Wide / landscape ticket
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # =========================================================
    # COLORS
    # =========================================================

    BLACK = colors.HexColor("#171717")
    WHITE = colors.white
    BLUE = colors.HexColor("#2563EB")
    LIGHT_BLUE = colors.HexColor("#EFF6FF")
    CREAM = colors.HexColor("#F5F1EA")
    GRAY = colors.HexColor("#6B7280")
    LIGHT_GRAY = colors.HexColor("#D1D5DB")

    # =========================================================
    # TICKET DIMENSIONS
    # =========================================================

    ticket_x = 28
    ticket_y = 100

    ticket_width = width - 56
    ticket_height = 320

    left_strip_width = 70
    stub_width = 175

    main_x = ticket_x + left_strip_width
    stub_x = ticket_x + ticket_width - stub_width

    # =========================================================
    # MAIN TICKET BACKGROUND
    # =========================================================

    pdf.setFillColor(WHITE)
    pdf.setStrokeColor(LIGHT_GRAY)
    pdf.setLineWidth(1)

    pdf.roundRect(
        ticket_x,
        ticket_y,
        ticket_width,
        ticket_height,
        10,
        fill=1,
        stroke=1,
    )

    # =========================================================
    # LEFT BLACK TICKET NUMBER STRIP
    # =========================================================

    pdf.setFillColor(BLACK)

    pdf.roundRect(
        ticket_x,
        ticket_y,
        left_strip_width,
        ticket_height,
        10,
        fill=1,
        stroke=0,
    )

    # Remove rounding on right side of strip
    pdf.rect(
        ticket_x + left_strip_width - 10,
        ticket_y,
        10,
        ticket_height,
        fill=1,
        stroke=0,
    )

    # Ticket number vertically
    pdf.saveState()

    pdf.translate(
        ticket_x + 35,
        ticket_y + 65,
    )

    pdf.rotate(90)

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(
        0,
        0,
        f"TV-{booking.id:08d}",
    )

    pdf.restoreState()

    # "TICKET NUMBER"
    pdf.saveState()

    pdf.translate(
        ticket_x + 35,
        ticket_y + 185,
    )

    pdf.rotate(90)

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica", 8)

    pdf.drawString(
        0,
        0,
        "TICKET NUMBER",
    )

    pdf.restoreState()

    # =========================================================
    # MAIN CONTENT AREA
    # =========================================================

    content_x = main_x + 28

    # =========================================================
    # BRANDING
    # =========================================================

    brand_y = ticket_y + ticket_height - 42

    # Blue logo box
    pdf.setFillColor(BLUE)

    pdf.roundRect(
        content_x,
        brand_y - 14,
        25,
        25,
        5,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 17)

    pdf.drawCentredString(
        content_x + 12.5,
        brand_y - 7,
        "T",
    )

    # TicketVault text
    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 17)

    pdf.drawString(
        content_x + 34,
        brand_y - 4,
        "Ticket",
    )

    pdf.setFillColor(BLUE)

    pdf.drawString(
        content_x + 82,
        brand_y - 4,
        "Vault",
    )

    # Tagline
    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica", 6.5)

    pdf.drawString(
        content_x + 34,
        brand_y - 17,
        "Secure. Reliable. Hassle-free ticketing.",
    )

    # =========================================================
    # EVENT TITLE
    # =========================================================

    title_y = ticket_y + ticket_height - 100

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 25)

    title = str(event.title)

    # Split long event title into two lines
    words = title.split()

    line1 = ""
    line2 = ""

    for word in words:
        test = f"{line1} {word}".strip()

        if len(test) <= 25:
            line1 = test
        else:
            line2 = f"{line2} {word}".strip()

    pdf.drawString(
        content_x,
        title_y,
        line1,
    )

    if line2:
        pdf.drawString(
            content_x,
            title_y - 34,
            line2,
        )

    # =========================================================
    # LIVE WORKSHOP INDICATOR
    # =========================================================

    live_x = stub_x - 155
    live_y = title_y + 4

    pdf.setFillColor(BLUE)

    pdf.circle(
        live_x,
        live_y,
        6,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(
        live_x + 15,
        live_y - 4,
        "Live workshop",
    )

    # =========================================================
    # EVENT DATE
    # =========================================================

    event_date = getattr(
        event,
        "event_date",
        None,
    )

    if event_date:
        date_text = event_date.strftime(
            "%B %d, %Y"
        ).upper()

        time_text = event_date.strftime(
            "%I:%M %p"
        )
    else:
        date_text = "DATE N/A"
        time_text = "TIME N/A"

    date_box_x = content_x
    date_box_y = ticket_y + 140

    date_box_width = 265
    date_box_height = 45

    pdf.setFillColor(CREAM)

    pdf.rect(
        date_box_x,
        date_box_y,
        date_box_width,
        date_box_height,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawCentredString(
        date_box_x + date_box_width / 2,
        date_box_y + 16,
        date_text,
    )

    # =========================================================
    # INFORMATION ROW
    # =========================================================

    info_y = ticket_y + 92

    # Top divider
    pdf.setStrokeColor(LIGHT_GRAY)
    pdf.setLineWidth(1)

    pdf.line(
        content_x,
        info_y + 32,
        stub_x - 25,
        info_y + 32,
    )

    # Column positions
    time_x = content_x
    price_x = content_x + 180
    seat_x = content_x + 360

    # TIME
    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica-Bold", 7)

    pdf.drawString(
        time_x,
        info_y + 12,
        "TIME",
    )

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        time_x,
        info_y - 5,
        time_text,
    )

    # Vertical divider
    pdf.setStrokeColor(LIGHT_GRAY)

    pdf.line(
        price_x - 25,
        info_y - 10,
        price_x - 25,
        info_y + 25,
    )

    # PRICE
    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica-Bold", 7)

    pdf.drawString(
        price_x,
        info_y + 12,
        "PRICE",
    )

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        price_x,
        info_y - 5,
        f"INR {booking.total_amount}",
    )

    # Vertical divider
    pdf.line(
        seat_x - 25,
        info_y - 10,
        seat_x - 25,
        info_y + 25,
    )

    # SEAT
    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica-Bold", 7)

    pdf.drawString(
        seat_x,
        info_y + 12,
        "SEAT",
    )

    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 13)

    pdf.drawString(
        seat_x,
        info_y - 6,
        f"{seat.row_label}{seat.seat_number}",
    )

    # =========================================================
    # ADDRESS
    # =========================================================

    address_y = ticket_y + 40

    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica-Bold", 7)

    pdf.drawString(
        content_x,
        address_y + 15,
        "ADDRESS",
    )

    venue = getattr(
        event,
        "venue",
        None,
    )

    venue_name = getattr(
        venue,
        "name",
        None,
    ) or "TicketVault Event"

    venue_address = getattr(
        venue,
        "address",
        None,
    ) or "Event Venue"

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica", 9)

    pdf.drawString(
        content_x,
        address_y,
        str(venue_name),
    )

    pdf.drawString(
        content_x,
        address_y - 12,
        str(venue_address),
    )

    # =========================================================
    # FOOTER BRANDING BAR
    # =========================================================

    footer_height = 32

    pdf.setFillColor(BLACK)

    pdf.rect(
        main_x,
        ticket_y,
        stub_x - main_x,
        footer_height,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 8)

    pdf.drawString(
        content_x,
        ticket_y + 11,
        "★  PLEASE PRESENT THIS QR CODE AT THE ENTRANCE",
    )

    pdf.setFillColor(BLUE)
    pdf.drawRightString(
        stub_x - 18,
        ticket_y + 11,
        "TICKETVAULT",
    )

    # =========================================================
    # RIGHT TICKET STUB
    # =========================================================

    pdf.setFillColor(CREAM)

    pdf.rect(
        stub_x,
        ticket_y,
        stub_width,
        ticket_height,
        fill=1,
        stroke=0,
    )

    # Recreate rounded right edge
    pdf.setFillColor(CREAM)

    pdf.roundRect(
        stub_x,
        ticket_y,
        stub_width,
        ticket_height,
        10,
        fill=1,
        stroke=0,
    )

    # =========================================================
    # PERFORATED DIVIDER
    # =========================================================

    pdf.setStrokeColor(BLACK)
    pdf.setLineWidth(1.5)
    pdf.setDash(5, 5)

    pdf.line(
        stub_x,
        ticket_y + 12,
        stub_x,
        ticket_y + ticket_height - 12,
    )

    pdf.setDash()

    # =========================================================
    # STUB INFORMATION
    # =========================================================

    stub_center = stub_x + stub_width / 2

    stub_top = ticket_y + ticket_height - 45

    # GATE
    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 8)

    pdf.drawString(
        stub_x + 25,
        stub_top,
        "GATE",
    )

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawRightString(
        stub_x + stub_width - 25,
        stub_top - 3,
        "01",
    )

    # Divider
    pdf.setStrokeColor(LIGHT_GRAY)

    pdf.line(
        stub_x + 22,
        stub_top - 20,
        stub_x + stub_width - 22,
        stub_top - 20,
    )

    # ROW
    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 8)

    pdf.drawString(
        stub_x + 25,
        stub_top - 48,
        "ROW",
    )

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawRightString(
        stub_x + stub_width - 25,
        stub_top - 51,
        str(seat.row_label),
    )

    # Divider
    pdf.setStrokeColor(LIGHT_GRAY)

    pdf.line(
        stub_x + 22,
        stub_top - 68,
        stub_x + stub_width - 22,
        stub_top - 68,
    )

    # SEAT
    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 8)

    pdf.drawString(
        stub_x + 25,
        stub_top - 96,
        "SEAT",
    )

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawRightString(
        stub_x + stub_width - 25,
        stub_top - 99,
        str(seat.seat_number),
    )

    # =========================================================
    # QR SECTION
    # =========================================================

    qr_separator_y = ticket_y + 125

    pdf.setStrokeColor(BLACK)
    pdf.setDash(5, 5)

    pdf.line(
        stub_x + 18,
        qr_separator_y,
        stub_x + stub_width - 18,
        qr_separator_y,
    )

    pdf.setDash()

    # QR label
    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 9)

    pdf.drawCentredString(
        stub_center,
        qr_separator_y - 22,
        "SCAN FOR ENTRY",
    )

    # =========================================================
    # QR CODE
    # =========================================================

    qr_data = f"TICKETVAULT:BOOKING:{booking.id}"

    qr = qrcode.make(qr_data)

    qr_buffer = BytesIO()

    qr.save(
        qr_buffer,
        format="PNG",
    )

    qr_buffer.seek(0)

    qr_image = ImageReader(qr_buffer)

    qr_size = 82

    pdf.drawImage(
        qr_image,
        stub_center - qr_size / 2,
        ticket_y + 35,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto",
    )

    # =========================================================
    # TICKET ID
    # =========================================================

    pdf.setFillColor(BLACK)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawCentredString(
        stub_center,
        ticket_y + 20,
        f"TICKET #{booking.id}",
    )

    # =========================================================
    # SAVE PDF
    # =========================================================

    pdf.save()

    buffer.seek(0)

    return buffer.read()