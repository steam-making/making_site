import re
import requests
from django.conf import settings


class MedutechAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


# 학교/기관 이름 뒤에 흔히 붙는 유형 표기. 긴 표현부터 매칭되도록 길이순으로 정렬.
_NAME_SUFFIXES = sorted(
    ['초등학교', '중학교', '고등학교', '지역아동센터', '문화센터', '아동센터',
     '유치원', '초교', '중교', '센터', '초', '중', '고'],
    key=len, reverse=True,
)


def _normalize_school_name(name):
    """'화정남초등학교'와 '화정남초'처럼 표기만 다른 같은 학교명을 같은 값으로 취급하기 위한 정규화."""
    name = re.sub(r'\s+', '', name or '')
    for suffix in _NAME_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


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
    이름이 같은(표기 차이는 무시) 출첵마스터 학교를 찾아 자동으로 매핑을 생성한다.
    '화정남초등학교' <-> '화정남초'처럼 학교 유형 표기(초등학교/초/중학교 등)만
    다른 경우도 같은 학교로 인식한다. 정규화된 이름이 여러 학교와 겹치는 경우는
    잘못 연결될 위험이 있어 자동 매칭에서 제외하고 수동 연동으로 남겨둔다.
    이미 매핑되어 있는 출강장소는 건드리지 않는다.
    """
    from collections import defaultdict
    from teachers.models import TeachingInstitution
    from .models import MedutechAccount, MedutechSchoolMapping

    account = MedutechAccount.objects.filter(user=user).first()
    if not account:
        return 0, 0

    schools = get_schools(account.api_token)
    schools_by_norm = defaultdict(list)
    for school in schools:
        schools_by_norm[_normalize_school_name(school['name'])].append(school)

    institutions = TeachingInstitution.objects.filter(teacher=user)
    matched = 0
    for institution in institutions:
        if MedutechSchoolMapping.objects.filter(institution=institution).exists():
            continue
        candidates = schools_by_norm.get(_normalize_school_name(institution.name), [])
        if len(candidates) != 1:
            continue
        school = candidates[0]
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


def get_recent_students(api_token, medutech_school_id):
    """
    medutech.kr의 특정 학교 학생 명단을, 가장 최근에 등록/변경된 월 기준으로 가져온다.
    (예: 8월에 새로 엑셀등록/부서이동이 있었다면 8월 시점 기준 유효 명단만 반환)
    반환값: (items, month) — items의 학생 식별자는 'id' 키를 사용한다.
    """
    url = f"{_base_url()}/attendance/api/students/recent/"
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

    return data.get('items', []), data.get('month', '')
