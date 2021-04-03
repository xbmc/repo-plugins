# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
from resources.lib.addon.timedate import get_datetime_now, get_timedelta
from resources.lib.addon.cache import set_search_history, get_search_history
from resources.lib.addon.window import get_property
from resources.lib.tmdb.api import TMDb
from resources.lib.addon.plugin import ADDONPATH, ADDON, PLUGINPATH, convert_type
from resources.lib.addon.parser import try_int, encode_url
from resources.lib.addon.setutils import merge_two_dicts, split_items


RELATIVE_DATES = [
    'primary_release_date.gte', 'primary_release_date.lte', 'release_date.gte', 'release_date.lte',
    'air_date.gte', 'air_date.lte', 'first_air_date.gte', 'first_air_date.lte']


SORTBY_MOVIES = [
    'popularity.asc', 'popularity.desc', 'release_date.asc', 'release_date.desc', 'revenue.asc', 'revenue.desc',
    'primary_release_date.asc', 'primary_release_date.desc', 'original_title.asc', 'original_title.desc',
    'vote_average.asc', 'vote_average.desc', 'vote_count.asc', 'vote_count.desc']

SORTBY_TV = [
    'vote_average.desc', 'vote_average.asc', 'first_air_date.desc', 'first_air_date.asc',
    'popularity.desc', 'popularity.asc']


ALL_METHODS = [
    'open', 'with_separator', 'sort_by', 'add_rule', 'clear', 'save', 'with_cast', 'with_crew', 'with_people',
    'primary_release_year', 'primary_release_date.gte', 'primary_release_date.lte', 'release_date.gte', 'release_date.lte',
    'with_release_type', 'region', 'with_networks', 'air_date.gte', 'air_date.lte', 'first_air_date.gte',
    'first_air_date.lte', 'first_air_date_year', 'with_genres', 'without_genres', 'with_companies', 'with_keywords',
    'without_keywords', 'with_original_language', 'vote_count.gte', 'vote_count.lte', 'vote_average.gte',
    'vote_average.lte', 'with_runtime.gte', 'with_runtime.lte', 'save_index', 'save_label']


REGIONS = [
    {'id': 'AD', 'name': u'Andorra (AD)'},
    {'id': 'AE', 'name': u'United Arab Emirates (AE)'},
    {'id': 'AF', 'name': u'Afghanistan (AF)'},
    {'id': 'AG', 'name': u'Antigua and Barbuda (AG)'},
    {'id': 'AI', 'name': u'Anguilla (AI)'},
    {'id': 'AL', 'name': u'Albania (AL)'},
    {'id': 'AM', 'name': u'Armenia (AM)'},
    {'id': 'AO', 'name': u'Angola (AO)'},
    {'id': 'AQ', 'name': u'Antarctica (AQ)'},
    {'id': 'AR', 'name': u'Argentina (AR)'},
    {'id': 'AS', 'name': u'American Samoa (AS)'},
    {'id': 'AT', 'name': u'Austria (AT)'},
    {'id': 'AU', 'name': u'Australia (AU)'},
    {'id': 'AW', 'name': u'Aruba (AW)'},
    {'id': 'AX', 'name': u'Åland Islands (AX)'},
    {'id': 'AZ', 'name': u'Azerbaijan (AZ)'},
    {'id': 'BA', 'name': u'Bosnia and Herzegovina (BA)'},
    {'id': 'BB', 'name': u'Barbados (BB)'},
    {'id': 'BD', 'name': u'Bangladesh (BD)'},
    {'id': 'BE', 'name': u'Belgium (BE)'},
    {'id': 'BF', 'name': u'Burkina Faso (BF)'},
    {'id': 'BG', 'name': u'Bulgaria (BG)'},
    {'id': 'BH', 'name': u'Bahrain (BH)'},
    {'id': 'BI', 'name': u'Burundi (BI)'},
    {'id': 'BJ', 'name': u'Benin (BJ)'},
    {'id': 'BL', 'name': u'Saint Barthélemy (BL)'},
    {'id': 'BM', 'name': u'Bermuda (BM)'},
    {'id': 'BN', 'name': u'Brunei Darussalam (BN)'},
    {'id': 'BO', 'name': u'Bolivia (BO)'},
    {'id': 'BQ', 'name': u'Bonaire (BQ)'},
    {'id': 'BR', 'name': u'Brazil (BR)'},
    {'id': 'BS', 'name': u'Bahamas (BS)'},
    {'id': 'BT', 'name': u'Bhutan (BT)'},
    {'id': 'BV', 'name': u'Bouvet Island (BV)'},
    {'id': 'BW', 'name': u'Botswana (BW)'},
    {'id': 'BY', 'name': u'Belarus (BY)'},
    {'id': 'BZ', 'name': u'Belize (BZ)'},
    {'id': 'CA', 'name': u'Canada (CA)'},
    {'id': 'CC', 'name': u'Cocos (CC)'},
    {'id': 'CD', 'name': u'Congo (CD)'},
    {'id': 'CF', 'name': u'Central African Republic (CF)'},
    {'id': 'CG', 'name': u'Congo (CG)'},
    {'id': 'CH', 'name': u'Switzerland (CH)'},
    {'id': 'CI', 'name': u'Côte d\'Ivoire (CI)'},
    {'id': 'CK', 'name': u'Cook Islands (CK)'},
    {'id': 'CL', 'name': u'Chile (CL)'},
    {'id': 'CM', 'name': u'Cameroon (CM)'},
    {'id': 'CN', 'name': u'China (CN)'},
    {'id': 'CO', 'name': u'Colombia (CO)'},
    {'id': 'CR', 'name': u'Costa Rica (CR)'},
    {'id': 'CU', 'name': u'Cuba (CU)'},
    {'id': 'CV', 'name': u'Cabo Verde (CV)'},
    {'id': 'CW', 'name': u'Curaçao (CW)'},
    {'id': 'CX', 'name': u'Christmas Island (CX)'},
    {'id': 'CY', 'name': u'Cyprus (CY)'},
    {'id': 'CZ', 'name': u'Czechia (CZ)'},
    {'id': 'DE', 'name': u'Germany (DE)'},
    {'id': 'DJ', 'name': u'Djibouti (DJ)'},
    {'id': 'DK', 'name': u'Denmark (DK)'},
    {'id': 'DM', 'name': u'Dominica (DM)'},
    {'id': 'DO', 'name': u'Dominican Republic (DO)'},
    {'id': 'DZ', 'name': u'Algeria (DZ)'},
    {'id': 'EC', 'name': u'Ecuador (EC)'},
    {'id': 'EE', 'name': u'Estonia (EE)'},
    {'id': 'EG', 'name': u'Egypt (EG)'},
    {'id': 'EH', 'name': u'Western Sahara (EH)'},
    {'id': 'ER', 'name': u'Eritrea (ER)'},
    {'id': 'ES', 'name': u'Spain (ES)'},
    {'id': 'ET', 'name': u'Ethiopia (ET)'},
    {'id': 'FI', 'name': u'Finland (FI)'},
    {'id': 'FJ', 'name': u'Fiji (FJ)'},
    {'id': 'FK', 'name': u'Falkland Islands (FK)'},
    {'id': 'FM', 'name': u'Micronesia (FM)'},
    {'id': 'FO', 'name': u'Faroe Islands (FO)'},
    {'id': 'FR', 'name': u'France (FR)'},
    {'id': 'GA', 'name': u'Gabon (GA)'},
    {'id': 'GB', 'name': u'United Kingdom (GB)'},
    {'id': 'GD', 'name': u'Grenada (GD)'},
    {'id': 'GE', 'name': u'Georgia (GE)'},
    {'id': 'GF', 'name': u'French Guiana (GF)'},
    {'id': 'GG', 'name': u'Guernsey (GG)'},
    {'id': 'GH', 'name': u'Ghana (GH)'},
    {'id': 'GI', 'name': u'Gibraltar (GI)'},
    {'id': 'GL', 'name': u'Greenland (GL)'},
    {'id': 'GM', 'name': u'Gambia (GM)'},
    {'id': 'GN', 'name': u'Guinea (GN)'},
    {'id': 'GP', 'name': u'Guadeloupe (GP)'},
    {'id': 'GQ', 'name': u'Equatorial Guinea (GQ)'},
    {'id': 'GR', 'name': u'Greece (GR)'},
    {'id': 'GS', 'name': u'South Georgia and the South Sandwich Islands (GS)'},
    {'id': 'GT', 'name': u'Guatemala (GT)'},
    {'id': 'GU', 'name': u'Guam (GU)'},
    {'id': 'GW', 'name': u'Guinea-Bissau (GW)'},
    {'id': 'GY', 'name': u'Guyana (GY)'},
    {'id': 'HK', 'name': u'Hong Kong (HK)'},
    {'id': 'HM', 'name': u'Heard Island and McDonald Islands (HM)'},
    {'id': 'HN', 'name': u'Honduras (HN)'},
    {'id': 'HR', 'name': u'Croatia (HR)'},
    {'id': 'HT', 'name': u'Haiti (HT)'},
    {'id': 'HU', 'name': u'Hungary (HU)'},
    {'id': 'ID', 'name': u'Indonesia (ID)'},
    {'id': 'IE', 'name': u'Ireland (IE)'},
    {'id': 'IL', 'name': u'Israel (IL)'},
    {'id': 'IM', 'name': u'Isle of Man (IM)'},
    {'id': 'IN', 'name': u'India (IN)'},
    {'id': 'IO', 'name': u'British Indian Ocean Territory (IO)'},
    {'id': 'IQ', 'name': u'Iraq (IQ)'},
    {'id': 'IR', 'name': u'Iran (IR)'},
    {'id': 'IS', 'name': u'Iceland (IS)'},
    {'id': 'IT', 'name': u'Italy (IT)'},
    {'id': 'JE', 'name': u'Jersey (JE)'},
    {'id': 'JM', 'name': u'Jamaica (JM)'},
    {'id': 'JO', 'name': u'Jordan (JO)'},
    {'id': 'JP', 'name': u'Japan (JP)'},
    {'id': 'KE', 'name': u'Kenya (KE)'},
    {'id': 'KG', 'name': u'Kyrgyzstan (KG)'},
    {'id': 'KH', 'name': u'Cambodia (KH)'},
    {'id': 'KI', 'name': u'Kiribati (KI)'},
    {'id': 'KM', 'name': u'Comoros (KM)'},
    {'id': 'KN', 'name': u'Saint Kitts and Nevis (KN)'},
    {'id': 'KP', 'name': u'Korea (KP)'},
    {'id': 'KR', 'name': u'Korea (KR)'},
    {'id': 'KW', 'name': u'Kuwait (KW)'},
    {'id': 'KY', 'name': u'Cayman Islands (KY)'},
    {'id': 'KZ', 'name': u'Kazakhstan (KZ)'},
    {'id': 'LA', 'name': u'Lao People\'s Democratic Republic (LA)'},
    {'id': 'LB', 'name': u'Lebanon (LB)'},
    {'id': 'LC', 'name': u'Saint Lucia (LC)'},
    {'id': 'LI', 'name': u'Liechtenstein (LI)'},
    {'id': 'LK', 'name': u'Sri Lanka (LK)'},
    {'id': 'LR', 'name': u'Liberia (LR)'},
    {'id': 'LS', 'name': u'Lesotho (LS)'},
    {'id': 'LT', 'name': u'Lithuania (LT)'},
    {'id': 'LU', 'name': u'Luxembourg (LU)'},
    {'id': 'LV', 'name': u'Latvia (LV)'},
    {'id': 'LY', 'name': u'Libya (LY)'},
    {'id': 'MA', 'name': u'Morocco (MA)'},
    {'id': 'MC', 'name': u'Monaco (MC)'},
    {'id': 'MD', 'name': u'Moldova (MD)'},
    {'id': 'ME', 'name': u'Montenegro (ME)'},
    {'id': 'MF', 'name': u'Saint Martin (MF)'},
    {'id': 'MG', 'name': u'Madagascar (MG)'},
    {'id': 'MH', 'name': u'Marshall Islands (MH)'},
    {'id': 'MK', 'name': u'North Macedonia (MK)'},
    {'id': 'ML', 'name': u'Mali (ML)'},
    {'id': 'MM', 'name': u'Myanmar (MM)'},
    {'id': 'MN', 'name': u'Mongolia (MN)'},
    {'id': 'MO', 'name': u'Macao (MO)'},
    {'id': 'MP', 'name': u'Northern Mariana Islands (MP)'},
    {'id': 'MQ', 'name': u'Martinique (MQ)'},
    {'id': 'MR', 'name': u'Mauritania (MR)'},
    {'id': 'MS', 'name': u'Montserrat (MS)'},
    {'id': 'MT', 'name': u'Malta (MT)'},
    {'id': 'MU', 'name': u'Mauritius (MU)'},
    {'id': 'MV', 'name': u'Maldives (MV)'},
    {'id': 'MW', 'name': u'Malawi (MW)'},
    {'id': 'MX', 'name': u'Mexico (MX)'},
    {'id': 'MY', 'name': u'Malaysia (MY)'},
    {'id': 'MZ', 'name': u'Mozambique (MZ)'},
    {'id': 'NA', 'name': u'Namibia (NA)'},
    {'id': 'NC', 'name': u'New Caledonia (NC)'},
    {'id': 'NE', 'name': u'Niger (NE)'},
    {'id': 'NF', 'name': u'Norfolk Island (NF)'},
    {'id': 'NG', 'name': u'Nigeria (NG)'},
    {'id': 'NI', 'name': u'Nicaragua (NI)'},
    {'id': 'NL', 'name': u'Netherlands (NL)'},
    {'id': 'NO', 'name': u'Norway (NO)'},
    {'id': 'NP', 'name': u'Nepal (NP)'},
    {'id': 'NR', 'name': u'Nauru (NR)'},
    {'id': 'NU', 'name': u'Niue (NU)'},
    {'id': 'NZ', 'name': u'New Zealand (NZ)'},
    {'id': 'OM', 'name': u'Oman (OM)'},
    {'id': 'PA', 'name': u'Panama (PA)'},
    {'id': 'PE', 'name': u'Peru (PE)'},
    {'id': 'PF', 'name': u'French Polynesia (PF)'},
    {'id': 'PG', 'name': u'Papua New Guinea (PG)'},
    {'id': 'PH', 'name': u'Philippines (PH)'},
    {'id': 'PK', 'name': u'Pakistan (PK)'},
    {'id': 'PL', 'name': u'Poland (PL)'},
    {'id': 'PM', 'name': u'Saint Pierre and Miquelon (PM)'},
    {'id': 'PN', 'name': u'Pitcairn (PN)'},
    {'id': 'PR', 'name': u'Puerto Rico (PR)'},
    {'id': 'PS', 'name': u'Palestine (PS)'},
    {'id': 'PT', 'name': u'Portugal (PT)'},
    {'id': 'PW', 'name': u'Palau (PW)'},
    {'id': 'PY', 'name': u'Paraguay (PY)'},
    {'id': 'QA', 'name': u'Qatar (QA)'},
    {'id': 'RE', 'name': u'Réunion (RE)'},
    {'id': 'RO', 'name': u'Romania (RO)'},
    {'id': 'RS', 'name': u'Serbia (RS)'},
    {'id': 'RU', 'name': u'Russian Federation (RU)'},
    {'id': 'RW', 'name': u'Rwanda (RW)'},
    {'id': 'SA', 'name': u'Saudi Arabia (SA)'},
    {'id': 'SB', 'name': u'Solomon Islands (SB)'},
    {'id': 'SC', 'name': u'Seychelles (SC)'},
    {'id': 'SD', 'name': u'Sudan (SD)'},
    {'id': 'SE', 'name': u'Sweden (SE)'},
    {'id': 'SG', 'name': u'Singapore (SG)'},
    {'id': 'SH', 'name': u'Saint Helena (SH)'},
    {'id': 'SI', 'name': u'Slovenia (SI)'},
    {'id': 'SJ', 'name': u'Svalbard and Jan Mayen (SJ)'},
    {'id': 'SK', 'name': u'Slovakia (SK)'},
    {'id': 'SL', 'name': u'Sierra Leone (SL)'},
    {'id': 'SM', 'name': u'San Marino (SM)'},
    {'id': 'SN', 'name': u'Senegal (SN)'},
    {'id': 'SO', 'name': u'Somalia (SO)'},
    {'id': 'SR', 'name': u'Suriname (SR)'},
    {'id': 'SS', 'name': u'South Sudan (SS)'},
    {'id': 'ST', 'name': u'Sao Tome and Principe (ST)'},
    {'id': 'SV', 'name': u'El Salvador (SV)'},
    {'id': 'SX', 'name': u'Sint Maarten (SX)'},
    {'id': 'SY', 'name': u'Syrian Arab Republic (SY)'},
    {'id': 'SZ', 'name': u'Eswatini (SZ)'},
    {'id': 'TC', 'name': u'Turks and Caicos Islands (TC)'},
    {'id': 'TD', 'name': u'Chad (TD)'},
    {'id': 'TF', 'name': u'French Southern Territories (TF)'},
    {'id': 'TG', 'name': u'Togo (TG)'},
    {'id': 'TH', 'name': u'Thailand (TH)'},
    {'id': 'TJ', 'name': u'Tajikistan (TJ)'},
    {'id': 'TK', 'name': u'Tokelau (TK)'},
    {'id': 'TL', 'name': u'Timor-Leste (TL)'},
    {'id': 'TM', 'name': u'Turkmenistan (TM)'},
    {'id': 'TN', 'name': u'Tunisia (TN)'},
    {'id': 'TO', 'name': u'Tonga (TO)'},
    {'id': 'TR', 'name': u'Turkey (TR)'},
    {'id': 'TT', 'name': u'Trinidad and Tobago (TT)'},
    {'id': 'TV', 'name': u'Tuvalu (TV)'},
    {'id': 'TW', 'name': u'Taiwan (TW)'},
    {'id': 'TZ', 'name': u'Tanzania (TZ)'},
    {'id': 'UA', 'name': u'Ukraine (UA)'},
    {'id': 'UG', 'name': u'Uganda (UG)'},
    {'id': 'US', 'name': u'United States of America (US)'},
    {'id': 'UY', 'name': u'Uruguay (UY)'},
    {'id': 'UZ', 'name': u'Uzbekistan (UZ)'},
    {'id': 'VA', 'name': u'Holy See (VA)'},
    {'id': 'VC', 'name': u'Saint Vincent and the Grenadines (VC)'},
    {'id': 'VE', 'name': u'Venezuela (VE)'},
    {'id': 'VG', 'name': u'Virgin Islands (VG)'},
    {'id': 'VI', 'name': u'Virgin Islands (VI)'},
    {'id': 'VN', 'name': u'Viet Nam (VN)'},
    {'id': 'VU', 'name': u'Vanuatu (VU)'},
    {'id': 'WF', 'name': u'Wallis and Futuna (WF)'},
    {'id': 'WS', 'name': u'Samoa (WS)'},
    {'id': 'YE', 'name': u'Yemen (YE)'},
    {'id': 'YT', 'name': u'Mayotte (YT)'},
    {'id': 'ZA', 'name': u'South Africa (ZA)'},
    {'id': 'ZM', 'name': u'Zambia (ZM)'},
    {'id': 'ZW', 'name': u'Zimbabwe (ZW)'}]


LANGUAGES = [
    {"id": "ab", "name": u"Abkhaz (ab)"},
    {"id": "aa", "name": u"Afar (aa)"},
    {"id": "af", "name": u"Afrikaans (af)"},
    {"id": "ak", "name": u"Akan (ak)"},
    {"id": "sq", "name": u"Albanian (sq)"},
    {"id": "am", "name": u"Amharic (am)"},
    {"id": "ar", "name": u"Arabic (ar)"},
    {"id": "an", "name": u"Aragonese (an)"},
    {"id": "hy", "name": u"Armenian (hy)"},
    {"id": "as", "name": u"Assamese (as)"},
    {"id": "av", "name": u"Avaric (av)"},
    {"id": "ae", "name": u"Avestan (ae)"},
    {"id": "ay", "name": u"Aymara (ay)"},
    {"id": "az", "name": u"Azerbaijani (az)"},
    {"id": "bm", "name": u"Bambara (bm)"},
    {"id": "ba", "name": u"Bashkir (ba)"},
    {"id": "eu", "name": u"Basque (eu)"},
    {"id": "be", "name": u"Belarusian (be)"},
    {"id": "bn", "name": u"Bengali; Bangla (bn)"},
    {"id": "bh", "name": u"Bihari (bh)"},
    {"id": "bi", "name": u"Bislama (bi)"},
    {"id": "bs", "name": u"Bosnian (bs)"},
    {"id": "br", "name": u"Breton (br)"},
    {"id": "bg", "name": u"Bulgarian (bg)"},
    {"id": "my", "name": u"Burmese (my)"},
    {"id": "ca", "name": u"Catalan; Valencian (ca)"},
    {"id": "ch", "name": u"Chamorro (ch)"},
    {"id": "ce", "name": u"Chechen (ce)"},
    {"id": "ny", "name": u"Chichewa; Chewa; Nyanja (ny)"},
    {"id": "zh", "name": u"Chinese (zh)"},
    {"id": "cv", "name": u"Chuvash (cv)"},
    {"id": "kw", "name": u"Cornish (kw)"},
    {"id": "co", "name": u"Corsican (co)"},
    {"id": "cr", "name": u"Cree (cr)"},
    {"id": "hr", "name": u"Croatian (hr)"},
    {"id": "cs", "name": u"Czech (cs)"},
    {"id": "da", "name": u"Danish (da)"},
    {"id": "dv", "name": u"Divehi; Dhivehi; Maldivian; (dv)"},
    {"id": "nl", "name": u"Dutch (nl)"},
    {"id": "dz", "name": u"Dzongkha (dz)"},
    {"id": "en", "name": u"English (en)"},
    {"id": "eo", "name": u"Esperanto (eo)"},
    {"id": "et", "name": u"Estonian (et)"},
    {"id": "ee", "name": u"Ewe (ee)"},
    {"id": "fo", "name": u"Faroese (fo)"},
    {"id": "fj", "name": u"Fijian (fj)"},
    {"id": "fi", "name": u"Finnish (fi)"},
    {"id": "fr", "name": u"French (fr)"},
    {"id": "ff", "name": u"Fula; Fulah; Pulaar; Pular (ff)"},
    {"id": "gl", "name": u"Galician (gl)"},
    {"id": "ka", "name": u"Georgian (ka)"},
    {"id": "de", "name": u"German (de)"},
    {"id": "el", "name": u"Greek, Modern (el)"},
    {"id": "gn", "name": u"GuaranÃ­ (gn)"},
    {"id": "gu", "name": u"Gujarati (gu)"},
    {"id": "ht", "name": u"Haitian; Haitian Creole (ht)"},
    {"id": "ha", "name": u"Hausa (ha)"},
    {"id": "he", "name": u"Hebrew (modern) (he)"},
    {"id": "hz", "name": u"Herero (hz)"},
    {"id": "hi", "name": u"Hindi (hi)"},
    {"id": "ho", "name": u"Hiri Motu (ho)"},
    {"id": "hu", "name": u"Hungarian (hu)"},
    {"id": "ia", "name": u"Interlingua (ia)"},
    {"id": "id", "name": u"Indonesian (id)"},
    {"id": "ie", "name": u"Interlingue (ie)"},
    {"id": "ga", "name": u"Irish (ga)"},
    {"id": "ig", "name": u"Igbo (ig)"},
    {"id": "ik", "name": u"Inupiaq (ik)"},
    {"id": "io", "name": u"Ido (io)"},
    {"id": "is", "name": u"Icelandic (is)"},
    {"id": "it", "name": u"Italian (it)"},
    {"id": "iu", "name": u"Inuktitut (iu)"},
    {"id": "ja", "name": u"Japanese (ja)"},
    {"id": "jv", "name": u"Javanese (jv)"},
    {"id": "kl", "name": u"Kalaallisut, Greenlandic (kl)"},
    {"id": "kn", "name": u"Kannada (kn)"},
    {"id": "kr", "name": u"Kanuri (kr)"},
    {"id": "ks", "name": u"Kashmiri (ks)"},
    {"id": "kk", "name": u"Kazakh (kk)"},
    {"id": "km", "name": u"Khmer (km)"},
    {"id": "ki", "name": u"Kikuyu, Gikuyu (ki)"},
    {"id": "rw", "name": u"Kinyarwanda (rw)"},
    {"id": "ky", "name": u"Kyrgyz (ky)"},
    {"id": "kv", "name": u"Komi (kv)"},
    {"id": "kg", "name": u"Kongo (kg)"},
    {"id": "ko", "name": u"Korean (ko)"},
    {"id": "ku", "name": u"Kurdish (ku)"},
    {"id": "kj", "name": u"Kwanyama, Kuanyama (kj)"},
    {"id": "la", "name": u"Latin (la)"},
    {"id": "lb", "name": u"Luxembourgish, Letzeburgesch (lb)"},
    {"id": "lg", "name": u"Ganda (lg)"},
    {"id": "li", "name": u"Limburgish, Limburgan, Limburger (li)"},
    {"id": "ln", "name": u"Lingala (ln)"},
    {"id": "lo", "name": u"Lao (lo)"},
    {"id": "lt", "name": u"Lithuanian (lt)"},
    {"id": "lu", "name": u"Luba-Katanga (lu)"},
    {"id": "lv", "name": u"Latvian (lv)"},
    {"id": "gv", "name": u"Manx (gv)"},
    {"id": "mk", "name": u"Macedonian (mk)"},
    {"id": "mg", "name": u"Malagasy (mg)"},
    {"id": "ms", "name": u"Malay (ms)"},
    {"id": "ml", "name": u"Malayalam (ml)"},
    {"id": "mt", "name": u"Maltese (mt)"},
    {"id": "mi", "name": u"MÄori (mi)"},
    {"id": "mr", "name": u"Marathi (MarÄá¹­hÄ«) (mr)"},
    {"id": "mh", "name": u"Marshallese (mh)"},
    {"id": "mn", "name": u"Mongolian (mn)"},
    {"id": "na", "name": u"Nauru (na)"},
    {"id": "nv", "name": u"Navajo, Navaho (nv)"},
    {"id": "nb", "name": u"Norwegian BokmÃ¥l (nb)"},
    {"id": "nd", "name": u"North Ndebele (nd)"},
    {"id": "ne", "name": u"Nepali (ne)"},
    {"id": "ng", "name": u"Ndonga (ng)"},
    {"id": "nn", "name": u"Norwegian Nynorsk (nn)"},
    {"id": "no", "name": u"Norwegian (no)"},
    {"id": "ii", "name": u"Nuosu (ii)"},
    {"id": "nr", "name": u"South Ndebele (nr)"},
    {"id": "oc", "name": u"Occitan (oc)"},
    {"id": "oj", "name": u"Ojibwe, Ojibwa (oj)"},
    {"id": "cu", "name": u"Old Church Slavonic, Church Slavic, Church Slavonic, Old Bulgarian, Old Slavonic (cu)"},
    {"id": "om", "name": u"Oromo (om)"},
    {"id": "or", "name": u"Oriya (or)"},
    {"id": "os", "name": u"Ossetian, Ossetic (os)"},
    {"id": "pa", "name": u"Panjabi, Punjabi (pa)"},
    {"id": "pi", "name": u"PÄli (pi)"},
    {"id": "fa", "name": u"Persian (Farsi) (fa)"},
    {"id": "pl", "name": u"Polish (pl)"},
    {"id": "ps", "name": u"Pashto, Pushto (ps)"},
    {"id": "pt", "name": u"Portuguese (pt)"},
    {"id": "qu", "name": u"Quechua (qu)"},
    {"id": "rm", "name": u"Romansh (rm)"},
    {"id": "rn", "name": u"Kirundi (rn)"},
    {"id": "ro", "name": u"Romanian, []) (ro)"},
    {"id": "ru", "name": u"Russian (ru)"},
    {"id": "sa", "name": u"Sanskrit (Saá¹ská¹›ta) (sa)"},
    {"id": "sc", "name": u"Sardinian (sc)"},
    {"id": "sd", "name": u"Sindhi (sd)"},
    {"id": "se", "name": u"Northern Sami (se)"},
    {"id": "sm", "name": u"Samoan (sm)"},
    {"id": "sg", "name": u"Sango (sg)"},
    {"id": "sr", "name": u"Serbian (sr)"},
    {"id": "gd", "name": u"Scottish Gaelic; Gaelic (gd)"},
    {"id": "sn", "name": u"Shona (sn)"},
    {"id": "si", "name": u"Sinhala, Sinhalese (si)"},
    {"id": "sk", "name": u"Slovak (sk)"},
    {"id": "sl", "name": u"Slovene (sl)"},
    {"id": "so", "name": u"Somali (so)"},
    {"id": "st", "name": u"Southern Sotho (st)"},
    {"id": "az", "name": u"South Azerbaijani (az)"},
    {"id": "es", "name": u"Spanish; Castilian (es)"},
    {"id": "su", "name": u"Sundanese (su)"},
    {"id": "sw", "name": u"Swahili (sw)"},
    {"id": "ss", "name": u"Swati (ss)"},
    {"id": "sv", "name": u"Swedish (sv)"},
    {"id": "ta", "name": u"Tamil (ta)"},
    {"id": "te", "name": u"Telugu (te)"},
    {"id": "tg", "name": u"Tajik (tg)"},
    {"id": "th", "name": u"Thai (th)"},
    {"id": "ti", "name": u"Tigrinya (ti)"},
    {"id": "bo", "name": u"Tibetan Standard, Tibetan, Central (bo)"},
    {"id": "tk", "name": u"Turkmen (tk)"},
    {"id": "tl", "name": u"Tagalog (tl)"},
    {"id": "tn", "name": u"Tswana (tn)"},
    {"id": "to", "name": u"Tonga (Tonga Islands) (to)"},
    {"id": "tr", "name": u"Turkish (tr)"},
    {"id": "ts", "name": u"Tsonga (ts)"},
    {"id": "tt", "name": u"Tatar (tt)"},
    {"id": "tw", "name": u"Twi (tw)"},
    {"id": "ty", "name": u"Tahitian (ty)"},
    {"id": "ug", "name": u"Uyghur, Uighur (ug)"},
    {"id": "uk", "name": u"Ukrainian (uk)"},
    {"id": "ur", "name": u"Urdu (ur)"},
    {"id": "uz", "name": u"Uzbek (uz)"},
    {"id": "ve", "name": u"Venda (ve)"},
    {"id": "vi", "name": u"Vietnamese (vi)"},
    {"id": "vo", "name": u"VolapÃ¼k (vo)"},
    {"id": "wa", "name": u"Walloon (wa)"},
    {"id": "cy", "name": u"Welsh (cy)"},
    {"id": "wo", "name": u"Wolof (wo)"},
    {"id": "fy", "name": u"Western Frisian (fy)"},
    {"id": "xh", "name": u"Xhosa (xh)"},
    {"id": "yi", "name": u"Yiddish (yi)"},
    {"id": "yo", "name": u"Yoruba (yo)"},
    {"id": "za", "name": u"Zhuang, Chuang (za)"},
    {"id": "zu", "name": u"Zulu (zu)"}]


def _get_release_types():
    return [
        {'id': 1, 'name': ADDON.getLocalizedString(32242)},
        {'id': 2, 'name': ADDON.getLocalizedString(32243)},
        {'id': 3, 'name': ADDON.getLocalizedString(32244)},
        {'id': 4, 'name': ADDON.getLocalizedString(32245)},
        {'id': 5, 'name': ADDON.getLocalizedString(32246)},
        {'id': 6, 'name': xbmc.getLocalizedString(36037)}]


def _get_basedir_top(tmdb_type):
    return [
        {
            'label': ADDON.getLocalizedString(32238).format(convert_type(tmdb_type, 'plural')),
            'art': {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)},
            'params': {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': 'open'}},
        {
            'label': ADDON.getLocalizedString(32239),
            'art': {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)},
            'params': {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': 'with_separator'}},
        {
            'label': ADDON.getLocalizedString(32240),
            'art': {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)},
            'params': {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': 'sort_by'}}]


def _get_basedir_end(tmdb_type):
    return [
        {
            'label': ADDON.getLocalizedString(32277),
            'art': {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)},
            'params': {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': 'add_rule'}},
        {
            'label': xbmc.getLocalizedString(192),
            'art': {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)},
            'params': {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': 'clear'}},
        {
            'label': xbmc.getLocalizedString(190),
            'art': {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)},
            'params': {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': 'save'}}]


def _get_basedir_rules_movies():
    return [
        {'label': ADDON.getLocalizedString(32247), 'method': 'with_cast'},
        {'label': ADDON.getLocalizedString(32248), 'method': 'with_crew'},
        {'label': ADDON.getLocalizedString(32249), 'method': 'with_people'},
        {'label': ADDON.getLocalizedString(32250), 'method': 'primary_release_year'},
        {'label': ADDON.getLocalizedString(32251), 'method': 'primary_release_date.gte'},
        {'label': ADDON.getLocalizedString(32252), 'method': 'primary_release_date.lte'},
        {'label': ADDON.getLocalizedString(32253), 'method': 'release_date.gte'},
        {'label': ADDON.getLocalizedString(32254), 'method': 'release_date.lte'},
        {'label': ADDON.getLocalizedString(32255), 'method': 'with_release_type'},
        {'label': ADDON.getLocalizedString(32256), 'method': 'region'}]


def _get_basedir_rules_tv():
    return [
        {'label': ADDON.getLocalizedString(32257), 'method': 'with_networks'},
        {'label': ADDON.getLocalizedString(32258), 'method': 'air_date.gte'},
        {'label': ADDON.getLocalizedString(32259), 'method': 'air_date.lte'},
        {'label': ADDON.getLocalizedString(32260), 'method': 'first_air_date.gte'},
        {'label': ADDON.getLocalizedString(32261), 'method': 'first_air_date.lte'},
        {'label': ADDON.getLocalizedString(32262), 'method': 'first_air_date_year'}]


def _get_basedir_rules(tmdb_type):
    items = [
        {'label': ADDON.getLocalizedString(32263), 'method': 'with_genres'},
        {'label': ADDON.getLocalizedString(32264), 'method': 'without_genres'},
        {'label': ADDON.getLocalizedString(32265), 'method': 'with_companies'},
        {'label': ADDON.getLocalizedString(32268), 'method': 'with_keywords'},
        {'label': ADDON.getLocalizedString(32267), 'method': 'without_keywords'}]
    items += _get_basedir_rules_movies() if tmdb_type == 'movie' else _get_basedir_rules_tv()
    items += [
        {'label': ADDON.getLocalizedString(32269), 'method': 'with_original_language'},
        {'label': ADDON.getLocalizedString(32270), 'method': 'vote_count.gte'},
        {'label': ADDON.getLocalizedString(32271), 'method': 'vote_count.lte'},
        {'label': ADDON.getLocalizedString(32272), 'method': 'vote_average.gte'},
        {'label': ADDON.getLocalizedString(32273), 'method': 'vote_average.lte'},
        {'label': ADDON.getLocalizedString(32274), 'method': 'with_runtime.gte'},
        {'label': ADDON.getLocalizedString(32275), 'method': 'with_runtime.lte'}]
    return items


def _get_basedir_add(tmdb_type):
    basedir_items = []
    for i in _get_basedir_rules(tmdb_type):
        if not _win_prop(i.get('method')):
            continue
        i['params'] = {'info': 'user_discover', 'tmdb_type': tmdb_type, 'method': i.pop('method', None)}
        basedir_items.append(i)
    return basedir_items


def _get_formatted_item(item):
    affix = _win_prop(item.get('params', {}).get('method'), 'Label')
    if affix:
        item['label'] = u'{}: {}'.format(item.get('label'), affix)
    return item


def _get_discover_params(tmdb_type, get_labels=False):
    params = {} if get_labels else {'info': 'discover', 'tmdb_type': tmdb_type, 'with_id': 'True'}
    rules = [{'method': 'with_separator'}, {'method': 'sort_by'}] + _get_basedir_rules(tmdb_type)
    for i in rules:
        method = i.pop('method', None)
        value = _win_prop(method, 'Label' if get_labels else None)
        if not value:
            continue
        params[method] = value
    return params


def _win_prop(name, prefix=None, **kwargs):
    if not name:
        return
    prefix = u'UserDiscover.{}'.format(prefix) if prefix else 'UserDiscover'
    return get_property(u'{}.{}'.format(prefix, name), **kwargs)


def _clear_properties(methods=ALL_METHODS):
    for method in methods:
        _win_prop(method, clear_property=True)
        _win_prop(method, 'Label', clear_property=True)


def _confirm_add(method):
    old_label = _win_prop(method, 'Label')
    old_value = _win_prop(method)
    if old_value or old_label:
        if xbmcgui.Dialog().yesno(
                method, '\n'.join([ADDON.getLocalizedString(32099), old_label, ADDON.getLocalizedString(32100)]),
                yeslabel=ADDON.getLocalizedString(32101), nolabel=ADDON.getLocalizedString(32102)):
            return False
    return True


def _get_query(tmdb_type, method, query=None, header=None, use_details=False):
    item = TMDb().get_tmdb_id_from_query(
        tmdb_type=tmdb_type,
        query=query or xbmcgui.Dialog().input(header),
        header=header or u'{} {}'.format(ADDON.getLocalizedString(32276), tmdb_type),
        use_details=use_details,
        get_listitem=True)
    if item and item.getUniqueID('tmdb'):
        return {'label': item.getLabel(), 'value': item.getUniqueID('tmdb'), 'method': method}


def _get_method(tmdb_type, method, header=None, use_details=False, confirmation=True):
    # If there's already values set then ask if the user wants to clear them instead of adding more
    if confirmation and not _confirm_add(method):
        return _clear_properties([method])

    # User inputs query, we look it up on TMDb and then ask them to select a choice
    properties = _get_query(tmdb_type, method, header=header, use_details=use_details)

    # Ask user if they want to try again if nothing selected or no results returned for query
    if not properties:
        if xbmcgui.Dialog().yesno(
                ADDON.getLocalizedString(32103),
                ADDON.getLocalizedString(32104).format(tmdb_type)):
            return _get_method(tmdb_type, method, header, use_details, confirmation=False)
        return

    return properties


def _select_method(tmdb_type, header=None):
    rules = _get_basedir_rules(tmdb_type)
    x = xbmcgui.Dialog().select(header, [i.get('label') for i in rules])
    if x != -1:
        return rules[x].get('method')


def _set_rule(method, label, value, overwrite=False):
    if not label or not value or not method:
        return
    old_value = None if overwrite else _win_prop(method)
    old_label = None if overwrite else _win_prop(method, 'Label')
    values = u'{} / {}'.format(old_value, value) if old_value else u'{}'.format(value)
    labels = u'{} / {}'.format(old_label, label) if old_label else label
    _win_prop(method, set_property=values)
    _win_prop(method, 'Label', set_property=labels)


def _select_properties_dialog(data_list, header=None, multiselect=True):
    if not data_list:
        return
    func = xbmcgui.Dialog().multiselect if multiselect else xbmcgui.Dialog().select
    header = header or ADDON.getLocalizedString(32111)
    dialog_list = [i.get('name') for i in data_list]
    select_list = func(header, dialog_list)
    if (multiselect and not select_list) or (not multiselect and select_list == -1):
        return
    if not multiselect:
        select_list = [select_list]
    return select_list


def _select_properties(data_list, method, header=None, multiselect=True):
    select_list = _select_properties_dialog(data_list, header, multiselect)
    if not select_list:
        return
    labels, values = None, None
    for i in select_list:
        label = data_list[i].get('name')
        value = data_list[i].get('id')
        if not value:
            continue
        labels = u'{} / {}'.format(labels, label) if labels else label
        values = u'{} / {}'.format(values, value) if values else u'{}'.format(value)
    if labels and values:
        return {'label': labels, 'value': values, 'method': method}


def _get_genre(tmdb_type, method):
    data_list = TMDb().get_request_lc('genre', tmdb_type, 'list')
    if data_list and data_list.get('genres'):
        return _select_properties(data_list['genres'], method, header=ADDON.getLocalizedString(32112))


def _get_sorting(tmdb_type):
    sort_method_list = SORTBY_MOVIES if tmdb_type == 'movie' else SORTBY_TV
    sort_method = xbmcgui.Dialog().select(xbmc.getLocalizedString(39010), sort_method_list)
    if sort_method != -1:
        return {'value': sort_method_list[sort_method], 'label': sort_method_list[sort_method], 'method': 'sort_by'}


def _get_separator():
    if xbmcgui.Dialog().yesno(
            ADDON.getLocalizedString(32107), ADDON.getLocalizedString(32108),
            yeslabel=ADDON.getLocalizedString(32109), nolabel=ADDON.getLocalizedString(32110)):
        return {'value': 'OR', 'label': 'ANY', 'method': 'with_separator'}
    return {'value': 'AND', 'label': 'ALL', 'method': 'with_separator'}


def _get_numeric(method, header=None):
    value = xbmcgui.Dialog().input(
        header, type=xbmcgui.INPUT_NUMERIC, defaultt=_win_prop(method))
    return {'value': value, 'label': value, 'method': method}


def _get_keyboard(method, header=None):
    value = xbmcgui.Dialog().input(
        header, defaultt=_win_prop(method))
    return {'value': value, 'label': value, 'method': method}


def _edit_rules(idx=-1):
    """ Need to setup window properties if editing """
    if idx == -1:
        return
    history = get_search_history('discover')
    history.reverse()
    try:
        item = history[idx]
    except IndexError:
        return
    _win_prop('save_index', set_property=u'{}'.format(len(history) - 1 - idx))
    _win_prop('save_label', set_property=u'{}'.format(item.get('label')))
    for k, v in item.get('params', {}).items():
        if k in ['info', 'tmdb_type']:
            continue
        _win_prop(k, set_property=v)
        _win_prop(k, 'Label', set_property=item.get('labels', {}).get(k, v))


def _save_rules(tmdb_type):
    my_idx = try_int(_win_prop('save_index'), fallback=-1)
    params = _get_discover_params(tmdb_type)
    labels = _get_discover_params(tmdb_type, get_labels=True)
    label = _win_prop('save_label') if my_idx != -1 else xbmcgui.Dialog().input(ADDON.getLocalizedString(32241))
    set_search_history(
        'discover',
        query={'label': label, 'params': params, 'labels': labels},
        replace=my_idx if my_idx != -1 else False)
    xbmcgui.Dialog().ok(u'{} {}'.format(xbmc.getLocalizedString(35259), label), u'{}'.format(params))


def _add_rule(tmdb_type, method=None):
    if not method or method == 'add_rule':
        method = _select_method(tmdb_type, header=ADDON.getLocalizedString(32277))
    if not method:
        return
    rules = None
    overwrite = True
    if method == 'sort_by':
        rules = _get_sorting(tmdb_type)
    elif method == 'with_separator':
        rules = _get_separator()
    elif method in ['with_genres', 'without_genres']:
        rules = _get_genre(tmdb_type, method)
    elif method in ['with_cast', 'with_crew', 'with_people']:
        rules = _get_method('person', method, use_details=True)
        overwrite = False
    elif method == 'with_companies':
        rules = _get_method('company', method, use_details=False)
        overwrite = False
    elif method in ['with_keywords', 'without_keywords']:
        rules = _get_method('keyword', method, use_details=False)
        overwrite = False
    elif method == 'with_networks':
        rules = _get_keyboard(method, header=ADDON.getLocalizedString(32278))
    elif '_year' in method:
        rules = _get_numeric(method, header=ADDON.getLocalizedString(32279))
    elif 'vote_' in method or '_runtime' in method:
        rules = _get_numeric(method, header=xbmc.getLocalizedString(16028))
    elif '_date' in method:
        header = u'{} YYYY-MM-DD\n{}'.format(ADDON.getLocalizedString(32114), ADDON.getLocalizedString(32113))
        rules = _get_keyboard(method, header=header)
    elif method == 'with_release_type':
        rules = _select_properties(_get_release_types(), method, header=ADDON.getLocalizedString(32119))
    elif method == 'region':
        rules = _select_properties(REGIONS, method, header=ADDON.getLocalizedString(32120), multiselect=False)
    elif method == 'with_original_language':
        rules = _select_properties(LANGUAGES, method, header=ADDON.getLocalizedString(32120), multiselect=False)
    if not rules or not rules.get('value'):
        return
    _set_rule(method, rules.get('label'), rules.get('value'), overwrite=overwrite)


def _translate_discover_params(tmdb_type, params):
    lookup_keyword = None if params.get('with_id') and params.get('with_id') != 'False' else 'keyword'
    lookup_company = None if params.get('with_id') and params.get('with_id') != 'False' else 'company'
    lookup_person = None if params.get('with_id') and params.get('with_id') != 'False' else 'person'
    lookup_genre = None if params.get('with_id') and params.get('with_id') != 'False' else 'genre'
    with_separator = params.get('with_separator')

    if params.get('with_genres'):
        params['with_genres'] = TMDb().get_translated_list(
            split_items(params.get('with_genres')), lookup_genre, separator=with_separator)

    if params.get('without_genres'):
        params['without_genres'] = TMDb().get_translated_list(
            split_items(params.get('without_genres')), lookup_genre, separator=with_separator)

    if params.get('with_keywords'):
        params['with_keywords'] = TMDb().get_translated_list(
            split_items(params.get('with_keywords')), lookup_keyword, separator=with_separator)

    if params.get('without_keywords'):
        params['without_keywords'] = TMDb().get_translated_list(
            split_items(params.get('without_keywords')), lookup_keyword, separator=with_separator)

    if params.get('with_companies'):
        params['with_companies'] = TMDb().get_translated_list(
            split_items(params.get('with_companies')), lookup_company, separator='NONE')

    if params.get('with_people'):
        params['with_people'] = TMDb().get_translated_list(
            split_items(params.get('with_people')), lookup_person, separator=with_separator)

    if params.get('with_cast'):
        params['with_cast'] = TMDb().get_translated_list(
            split_items(params.get('with_cast')), lookup_person, separator=with_separator)

    if params.get('with_crew'):
        params['with_crew'] = TMDb().get_translated_list(
            split_items(params.get('with_crew')), lookup_person, separator=with_separator)

    if params.get('with_release_type'):
        params['with_release_type'] = TMDb().get_translated_list(
            split_items(params.get('with_release_type')), None, separator='OR')

    # Translate relative dates based upon today's date
    for i in RELATIVE_DATES:
        datecode = params.get(i, '')
        datecode = datecode.lower()
        if not datecode or all(x not in datecode for x in ['t-', 't+']):
            continue  # No value or not a relative date so skip
        elif 't-' in datecode:
            days = try_int(datecode.replace('t-', ''))
            date = get_datetime_now() - get_timedelta(days=days)
        elif 't+' in datecode:
            days = try_int(datecode.replace('t+', ''))
            date = get_datetime_now() + get_timedelta(days=days)
        params[i] = date.strftime("%Y-%m-%d")

    return params


class UserDiscoverLists():
    def list_discover(self, tmdb_type, **kwargs):
        kwargs.pop('info', None)
        items = TMDb().get_discover_list(tmdb_type, **_translate_discover_params(tmdb_type, kwargs))
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        return items

    def list_discoverdir_router(self, **kwargs):
        if kwargs.get('clear_cache') != 'True' and kwargs.get('method') not in ['delete', 'rename']:
            return self.list_discoverdir(**kwargs)

        params = kwargs.copy()
        params.pop('clear_cache', None)
        params.pop('method', None)
        params.pop('idx', None)
        self.container_update = u'{},replace'.format(encode_url(PLUGINPATH, **params))

        if kwargs.get('clear_cache') == 'True':
            set_search_history('discover', clear_cache=True)

        elif kwargs.get('method') == 'delete':
            idx = try_int(kwargs.get('idx', -1))
            if idx == -1:
                return
            set_search_history('discover', replace=idx)

        elif kwargs.get('method') == 'rename':
            idx = try_int(kwargs.get('idx', -1))
            if idx == -1:
                return
            history = get_search_history('discover')
            try:
                item = history[idx]
            except IndexError:
                return
            if not item:
                return
            item['label'] = xbmcgui.Dialog().input('Rename', defaultt=item.get('label')) or item.get('label')
            set_search_history('discover', item, replace=idx)

    def list_discoverdir(self, **kwargs):
        items = []
        params = merge_two_dicts(kwargs, {'info': 'user_discover'})
        artwork = {'thumb': u'{}/resources/poster.png'.format(ADDONPATH)}
        for i in ['movie', 'tv']:
            item = {
                'label': u'{} {}'.format(ADDON.getLocalizedString(32174), convert_type(i, 'plural')),
                'params': merge_two_dicts(params, {'tmdb_type': i}),
                'infoproperties': {'specialsort': 'top'},
                'art': artwork}
            items.append(item)

        history = get_search_history('discover')
        history.reverse()
        for x, i in enumerate(history):
            item_params = merge_two_dicts(kwargs, i.get('params', {}))
            edit_params = {'info': 'user_discover', 'tmdb_type': item_params.get('tmdb_type'), 'method': 'edit', 'idx': x}
            name_params = {'info': 'dir_discover', 'tmdb_type': item_params.get('tmdb_type'), 'method': 'rename', 'idx': x}
            dele_params = {'info': 'dir_discover', 'tmdb_type': item_params.get('tmdb_type'), 'method': 'delete', 'idx': x}
            item = {
                'label': i.get('label'),
                'params': item_params,
                'art': artwork,
                'context_menu': [
                    (xbmc.getLocalizedString(21435), u'Container.Update({})'.format(encode_url(PLUGINPATH, **edit_params))),
                    (xbmc.getLocalizedString(118), u'Container.Update({})'.format(encode_url(PLUGINPATH, **name_params))),
                    (xbmc.getLocalizedString(117), u'Container.Update({})'.format(encode_url(PLUGINPATH, **dele_params)))]}
            items.append(item)
        if history:
            item = {
                'label': ADDON.getLocalizedString(32237),
                'art': artwork,
                'params': merge_two_dicts(params, {'info': 'dir_discover', 'clear_cache': 'True'})}
            items.append(item)
        return items

    def list_userdiscover(self, tmdb_type, **kwargs):
        method = kwargs.get('method')

        # Method routing
        if not method or method == 'clear':
            _clear_properties()
        elif method == 'save':
            _save_rules(tmdb_type)
        elif method == 'edit':
            _edit_rules(idx=try_int(kwargs.get('idx'), fallback=-1))
        else:
            _add_rule(tmdb_type, method)

        # Build directory items
        basedir_items = []
        basedir_items += _get_basedir_top(tmdb_type)
        basedir_items += _get_basedir_add(tmdb_type)
        basedir_items += _get_basedir_end(tmdb_type)

        self.update_listing = True if method and method != 'edit' else False
        self.container_content = 'files'

        items = [_get_formatted_item(i) for i in basedir_items]
        items[0]['params'] = _get_discover_params(tmdb_type)
        return items
