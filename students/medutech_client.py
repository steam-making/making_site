import requests
from django.conf import settings


class MedutechAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _base_url():
    return getattr(settings, 'MEDUTECH_API_BASE_URL', 'https://api.medutech.kr')


def _headers(api_token):
    return {'Authorization': f'Token {api_token}', 'Accept': 'application/json'}


def _parse_json(resp):
    try:
        return resp.json()
    except ValueError as exc:
        raise MedutechAPIError("medutech.kr에서 올바르지 않은 응답을 받았습니다.") from exc


def get_schools(api_token):
    """medutech.kr에 등록된 내 학교 목록: [{id, name, program_name}, ...]"""
    url = f"{_base_url()}/attendance/api/schools/"
    try:
        resp = requests.get(url, headers=_headers(api_token), timeout=10)
    except requests.RequestException as exc:
        raise MedutechAPIError(f"medutech.kr에 연결할 수 없습니다: {exc}") from exc

    if resp.status_code == 401:
        raise MedutechAPIError("API 토큰이 유효하지 않습니다.", status_code=401)
    if not resp.ok:
        raise MedutechAPIError(f"medutech.kr 응답 오류 ({resp.status_code})", status_code=resp.status_code)

    return _parse_json(resp).get('items', [])


def auto_match_schools(user):
    """
    출첵마스터 계정 연동 시 1회만 실행: 이 유저가 담당하는 출강장소 중
    이름이 정확히 일치하는 출첵마스터 학교를 찾아 자동으로 매핑을 생성한다.
    이미 매핑되어 있는 출강장소는 건드리지 않는다.
    """
    from teachers.models import TeachingInstitution
    from .models import MedutechAccount, MedutechSchoolMapping

    account = MedutechAccount.objects.filter(user=user).first()
    if not account:
        return 0, 0

    schools = get_schools(account.api_token)
    school_by_name = {s['name']: s for s in schools}

    institutions = TeachingInstitution.objects.filter(teacher=user)
    matched = 0
    for institution in institutions:
        if MedutechSchoolMapping.objects.filter(institution=institution).exists():
            continue
        school = school_by_name.get(institution.name)
        if not school:
            continue
        MedutechSchoolMapping.objects.update_or_create(
            institution=institution,
            defaults={
                'medutech_school_id': school['id'],
                'medutech_school_name': school['name'],
                'medutech_program_name': school.get('program_name', ''),
            }
        )
        matched += 1

    return matched, institutions.count()


def get_students_today(api_token, medutech_school_id):
    """medutech.kr의 특정 학교 학생 목록(오늘자 출석 상태 포함)을 가져온다."""
    url = f"{_base_url()}/attendance/api/students/today/"
    try:
        resp = requests.get(
            url,
            headers=_headers(api_token),
            params={'school_id': medutech_school_id},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise MedutechAPIError(f"medutech.kr에 연결할 수 없습니다: {exc}") from exc

    if resp.status_code == 401:
        raise MedutechAPIError("API 토큰이 유효하지 않습니다.", status_code=401)
    if not resp.ok:
        raise MedutechAPIError(f"medutech.kr 응답 오류 ({resp.status_code})", status_code=resp.status_code)

    data = _parse_json(resp)
    if not data.get('ok', True):
        raise MedutechAPIError(data.get('error', '알 수 없는 오류가 발생했습니다.'))

    return data.get('data', {}).get('items', [])
