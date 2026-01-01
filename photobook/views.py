# academy_site/photobook/views.py

from django.shortcuts import render
from django.http import FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
from fpdf import FPDF
import os, io

def upload_page(request):
    return render(request, 'photobook/upload.html')

@csrf_exempt
def create_photobook(request):
    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        if not files:
            return HttpResponse("사진이 업로드되지 않았습니다.", status=400)

        files.sort(key=lambda x: x.name)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=10)

        for f in files:
            img = Image.open(f)
            img_io = io.BytesIO()
            img.convert('RGB').save(img_io, format='JPEG')
            img_io.seek(0)

            filename = default_storage.save('temp.jpg', img_io)
            filepath = os.path.join(settings.MEDIA_ROOT, filename)

            pdf.add_page()
            pdf.image(filepath, x=10, y=10, w=180)

            os.remove(filepath)

        pdf_output = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        pdf_output.write(pdf_bytes)
        pdf_output.seek(0)

        return FileResponse(pdf_output, as_attachment=True, filename='photobook.pdf')
