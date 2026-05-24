/* global React, window */
// Static seed shapes for sample books, daily picks, sample TOC and page.
// DOMAINS lives in data-domains.js (loaded before this file).

const DOMAINS = window.SOL_FALLBACK_DOMAINS;

// Featured books, used in library pages and search results.
const BOOKS = [
  {
    urn: 'OXlyzwsl',
    title_ar: 'كتاب الرجال',
    title_en: 'Rijal al-Najashi',
    author: 'Ahmad ibn ʿAli al-Najashi',
    author_ar: 'أحمد بن علي النجاشي',
    death_year_ah: 450,
    death_year_ce: 1058,
    page_count: 624,
    category: 'shia-hadith-narrators',
    sect: 'Imami',
    madhab: null,
    canonical: 'primary',
    language: 'Arabic',
    blurb:
      'The foundational biographical dictionary of Imami narrators; a primary source for evaluating chains.',
  },
  {
    urn: 'TaqTah52',
    title_ar: 'تقريب التهذيب',
    title_en: 'Taqrib al-Tahdhib',
    author: 'Ibn Hajar al-ʿAsqalani',
    author_ar: 'ابن حجر العسقلاني',
    death_year_ah: 852,
    death_year_ce: 1449,
    page_count: 777,
    category: 'sunni-hadith-narrators',
    sect: 'Sunni',
    madhab: 'Shafiʿi',
    canonical: 'primary',
    language: 'Arabic',
    blurb: 'Condensed biographical evaluations of the narrators of the six canonical collections.',
  },
  {
    urn: 'KafSlm32',
    title_ar: 'الكافي',
    title_en: 'al-Kafi',
    author: 'Muhammad ibn Yaʿqub al-Kulayni',
    author_ar: 'محمد بن يعقوب الكليني',
    death_year_ah: 329,
    death_year_ce: 941,
    page_count: 2148,
    category: 'shia-hadith-general',
    sect: 'Imami',
    madhab: null,
    canonical: 'primary',
    language: 'Arabic',
    blurb:
      'The earliest of the Four Books of Twelver hadith; ~16,000 reports across uṣūl, furūʿ, and rawḍa.',
  },
  {
    urn: 'BukhJam2',
    title_ar: 'صحيح البخاري',
    title_en: 'Sahih al-Bukhari',
    author: 'Muhammad ibn Ismaʿil al-Bukhari',
    author_ar: 'محمد بن إسماعيل البخاري',
    death_year_ah: 256,
    death_year_ce: 870,
    page_count: 1814,
    category: 'sunni-hadith-general',
    sect: 'Sunni',
    madhab: null,
    canonical: 'primary',
    language: 'Arabic',
    blurb: 'The most widely cited hadith collection in Sunni tradition.',
  },
  {
    urn: 'FathBari',
    title_ar: 'فتح الباري بشرح صحيح البخاري',
    title_en: 'Fath al-Bari',
    author: 'Ibn Hajar al-ʿAsqalani',
    author_ar: 'ابن حجر العسقلاني',
    death_year_ah: 852,
    death_year_ce: 1449,
    page_count: 7800,
    category: 'sunni-hadith-general',
    sect: 'Sunni',
    madhab: 'Shafiʿi',
    canonical: 'primary',
    language: 'Arabic',
    blurb: 'The towering commentary on Sahih al-Bukhari; an encyclopedia of hadith sciences.',
  },
  {
    urn: 'WasShia',
    title_ar: 'وسائل الشيعة',
    title_en: 'Wasaʾil al-Shiʿa',
    author: 'al-Hurr al-ʿAmili',
    author_ar: 'الحر العاملي',
    death_year_ah: 1104,
    death_year_ce: 1693,
    page_count: 14200,
    category: 'shia-hadith-fiqh',
    sect: 'Imami',
    madhab: null,
    canonical: 'primary',
    language: 'Arabic',
    blurb: 'Topically arranged corpus of Imami legal hadith; ~36,000 reports.',
  },
  {
    urn: 'TafsTab',
    title_ar: 'جامع البيان',
    title_en: 'Jamiʿ al-Bayan',
    author: 'al-Tabari',
    author_ar: 'الطبري',
    death_year_ah: 310,
    death_year_ce: 923,
    page_count: 6300,
    category: 'sunni-tafsir',
    sect: 'Sunni',
    madhab: null,
    canonical: 'primary',
    language: 'Arabic',
    blurb: 'The earliest comprehensive Sunni tafsir; reports parallel exegetical traditions.',
  },
  {
    urn: 'MizanQM',
    title_ar: 'الميزان في تفسير القرآن',
    title_en: 'al-Mizan fi Tafsir al-Qurʾan',
    author: 'al-Tabatabaʾi',
    author_ar: 'الطباطبائي',
    death_year_ah: 1402,
    death_year_ce: 1981,
    page_count: 5400,
    category: 'shia-tafsir',
    sect: 'Imami',
    madhab: null,
    canonical: 'primary',
    language: 'Arabic',
    blurb: 'A 20th-c. tafsir interpreting Qurʾan-by-Qurʾan with extensive philosophical excurses.',
  },
];

// Sample hadith from al-Kafi, illustrative content for the reader.
const SAMPLE_TOC = [
  { page: 1, title: 'مقدمة المؤلف', title_en: 'Author’s Introduction' },
  { page: 11, title: 'كتاب العقل والجهل', title_en: 'The Book of Intellect and Ignorance' },
  { page: 47, title: 'كتاب فضل العلم', title_en: 'The Book of the Excellence of Knowledge' },
  { page: 109, title: 'كتاب التوحيد', title_en: 'The Book of Divine Unity', active: true },
  { page: 184, title: 'كتاب الحجة', title_en: 'The Book of Proof' },
  { page: 421, title: 'كتاب الإيمان والكفر', title_en: 'The Book of Faith and Disbelief' },
  { page: 612, title: 'كتاب الدعاء', title_en: 'The Book of Supplication' },
  { page: 738, title: 'كتاب فضل القرآن', title_en: 'The Book of the Excellence of the Qurʾan' },
  { page: 791, title: 'كتاب العشرة', title_en: 'The Book of Social Conduct' },
];

// Two pages of sample content (page 109 of al-Kafi, opening of Kitab al-Tawhid).
// Each entry is one hadith; isnad + matn separated.
const SAMPLE_PAGE = {
  page_number: 109,
  total_pages: 2148,
  chapter_title: 'كتاب التوحيد',
  chapter_title_en: 'The Book of Divine Unity',
  section_title: 'باب حدوث العالم وإثبات المُحدِث',
  section_title_en: 'Chapter: The contingency of the world and the affirmation of its Originator',
  hadiths: [
    {
      n: 1,
      isnad_ar:
        'عَلِيُّ بْنُ إِبْرَاهِيمَ، عَنْ أَبِيهِ، عَنِ الْعَبَّاسِ بْنِ عَمْرٍو الْفُقَيْمِيِّ، عَنْ هِشَامِ بْنِ الْحَكَمِ، فِي حَدِيثِ الزِّنْدِيقِ الَّذِي أَتَى أَبَا عَبْدِ اللَّهِ ﷷ',
      matn_ar:
        'فَكَانَ مِنْ سُؤَالِهِ أَنْ قَالَ: كَيْفَ يَعْبُدُ اللَّهَ الْخَلْقُ وَلَمْ يَرَوْهُ؟ قَالَ ﷷ: «رَأَتْهُ الْقُلُوبُ بِنُورِ الْإِيمَانِ، وَأَثْبَتَتْهُ الْعُقُولُ بِيَقَظَتِهَا إِثْبَاتَ الْعَيَانِ، وَالْأَبْصَارُ لَا تُدْرِكُهُ، وَهُوَ يُدْرِكُ الْأَبْصَارَ، وَهُوَ اللَّطِيفُ الْخَبِيرُ».',
      matn_en:
        'Among his questions was: “How can creation worship God whom they have not seen?” He (peace be upon him) replied: “Hearts have seen Him by the light of faith, and intellects have affirmed Him with their wakefulness as one affirms what is witnessed; sight does not perceive Him, yet He perceives sight, He is the Subtle, the Aware.”',
      narrators: [
        {
          name: 'Hisham ibn al-Hakam',
          name_ar: 'هشام بن الحكم',
          role: 'Companion of al-Sadiq',
          grade: 'Trustworthy',
          d: 199,
        },
        {
          name: 'al-ʿAbbas ibn ʿAmr al-Fuqaymi',
          name_ar: 'العباس بن عمرو الفقيمي',
          role: 'Transmitter',
          grade: 'Reliable',
          d: 270,
        },
        {
          name: 'Ibrahim ibn Hashim',
          name_ar: 'إبراهيم بن هاشم',
          role: 'Father of ʿAli',
          grade: 'Trustworthy',
          d: 245,
        },
        {
          name: 'ʿAli ibn Ibrahim al-Qummi',
          name_ar: 'علي بن إبراهيم القمي',
          role: 'Compiler’s teacher',
          grade: 'Trustworthy',
          d: 307,
        },
      ],
      grade: 'sahih',
      cross_refs: [
        {
          book: 'al-Tawhid (Saduq)',
          book_ar: 'التوحيد للصدوق',
          chapter: 'Bab al-Ruʾya',
          page: 108,
        },
        { book: 'Bihar al-Anwar', book_ar: 'بحار الأنوار', chapter: 'Vol. 4', page: 44 },
      ],
    },
    {
      n: 2,
      isnad_ar:
        'مُحَمَّدُ بْنُ يَحْيَى، عَنْ أَحْمَدَ بْنِ مُحَمَّدِ بْنِ عِيسَى، عَنِ ابْنِ أَبِي عُمَيْرٍ، عَنْ هِشَامِ بْنِ سَالِمٍ، عَنْ أَبِي عَبْدِ اللَّهِ ﷷ',
      matn_ar:
        'قَالَ: «إِنَّ اللَّهَ تَبَارَكَ وَتَعَالَى خَلْوٌ مِنْ خَلْقِهِ، وَخَلْقُهُ خَلْوٌ مِنْهُ، وَكُلُّ مَا وَقَعَ عَلَيْهِ اسْمُ شَيْءٍ مَا خَلَا اللَّهَ فَهُوَ مَخْلُوقٌ، وَاللَّهُ خَالِقُ كُلِّ شَيْءٍ، تَبَارَكَ الَّذِي لَيْسَ كَمِثْلِهِ شَيْءٌ».',
      matn_en:
        'He (peace be upon him) said: “God, Blessed and Exalted, is distinct from His creation, and His creation is distinct from Him. Everything to which the name ‘thing’ applies, save God, is created; and God is the Creator of every thing. Blessed is He: there is nothing like Him.”',
      narrators: [
        {
          name: 'Hisham ibn Salim',
          name_ar: 'هشام بن سالم',
          role: 'Companion of al-Sadiq',
          grade: 'Trustworthy',
          d: 179,
        },
        {
          name: 'Ibn Abi ʿUmayr',
          name_ar: 'ابن أبي عمير',
          role: 'Major transmitter',
          grade: 'Eminent',
          d: 217,
        },
        {
          name: 'Ahmad ibn Muhammad ibn ʿIsa',
          name_ar: 'أحمد بن محمد بن عيسى',
          role: 'Qummi authority',
          grade: 'Trustworthy',
          d: 280,
        },
        {
          name: 'Muhammad ibn Yahya al-ʿAttar',
          name_ar: 'محمد بن يحيى العطار',
          role: 'Compiler’s teacher',
          grade: 'Trustworthy',
          d: 290,
        },
      ],
      grade: 'sahih',
      cross_refs: [
        {
          book: 'al-Tawhid (Saduq)',
          book_ar: 'التوحيد للصدوق',
          chapter: 'Bab al-Tawhid',
          page: 105,
        },
      ],
    },
  ],
};

// Curated "today" picks — Verse, Hadith, and Book of the Day.
// Static at this point; rotates from a content calendar in production.
const DAILY = {
  // Hijri/Gregorian date display values
  date: {
    hijri: '15 Jumādā al-Ūlā 1446',
    hijri_short: '15 / V / 1446',
    gregorian: '17 November 2024',
  },

  verse: {
    surah: 'al-Mulk',
    surah_ar: 'الملك',
    surah_n: 67,
    ayah_n: 2,
    ayah_ar:
      'الَّذِي خَلَقَ الْمَوْتَ وَالْحَيَاةَ لِيَبْلُوَكُمْ أَيُّكُمْ أَحْسَنُ عَمَلًا ۚ وَهُوَ الْعَزِيزُ الْغَفُورُ',
    ayah_en:
      'He who created death and life to test which of you is best in deed. And He is the Mighty, the Forgiving.',
    // Two tafsir excerpts — one Sunni, one Imami — to surface comparative reading.
    tafsirs: [
      {
        book: 'al-Mizan fi Tafsir al-Qurʾan',
        book_ar: 'الميزان في تفسير القرآن',
        author: 'al-Tabatabaʾi',
        urn: 'MizanQM',
        excerpt_en:
          '“Best in deed” is not measured by abundance but by sincerity and conformity to what is right. Death is mentioned before life because the test demands awareness of finitude before living rightly within it.',
        excerpt_ar:
          '«أحسن عملا» لا يقاس بالكثرة بل بالإخلاص والانطباق على الحق؛ وقُدّم ذكر الموت لأن الاختبار يستدعي الوعي بالفناء قبل العيش في حدوده.',
      },
      {
        book: 'Jamiʿ al-Bayan',
        book_ar: 'جامع البيان',
        author: 'al-Tabari',
        urn: 'TafsTab',
        excerpt_en:
          'The created order — its mortality and its quickening — is itself the apparatus of the trial. The verse closes on al-ʿAzīz al-Ghafūr to anchor accountability between power and pardon.',
        excerpt_ar:
          'الخَلق بفنائه وحياته هو ذاته آلة الاختبار، وقد ختمت الآية بـ«العزيز الغفور» لتثبت المحاسبة بين القدرة والمغفرة.',
      },
    ],
  },

  hadith: {
    matn_ar: 'إنما الأعمال بالنيات',
    matn_en: 'Actions are but by intentions.',
    isnad_ar: 'عَنْ عُمَرَ بْنِ الْخَطَّابِ، عَنِ النَّبِيِّ ﷺ',
    source: {
      book: 'Bukhārī',
      book_ar: 'صحيح البخاري',
      n: '1.1.1',
      urn: 'BukhJam2',
      sect: 'Sunni',
    },
    parallels: [
      { book: 'Muslim', book_ar: 'صحيح مسلم', n: '1907', urn: null, sect: 'Sunni' },
      { book: 'al-Kāfī', book_ar: 'الكافي', n: '2/16/h.4', urn: 'KafSlm32', sect: 'Imami' },
    ],
    grade: 'sahih',
    grade_label: 'Ṣaḥīḥ',
    note: 'The opening hadith of Ṣaḥīḥ al-Bukhārī, transmitted from ʿUmar ibn al-Khaṭṭāb.',
  },

  book: {
    urn: 'KafSlm32',
    rationale:
      'The earliest of the Four Books — read today for its opening Kitāb al-ʿAql wa-l-Jahl, the intellect as the first of God’s creations.',
    open_to: { page: 109, chapter_en: 'Kitāb al-Tawḥīd' },
  },

  // Curated horizontal carousel — “In rotation today”.
  rotation: [
    'MizanQM',
    'KafSlm32',
    'BukhJam2',
    'WasShia',
    'TafsTab',
    'FathBari',
    'OXlyzwsl',
    'TaqTah52',
  ],
};

// ─── Backend wiring ───────────────────────────────────────────────
// The static globals above are the v1 seed / shape contract. The
// real backend at <API_BASE> serves the same shapes. As endpoints come
// online we replace the static fields below with fetched values.
//
// API_BASE resolves to the same host the page was loaded from, on port
// 8001 (uvicorn). For local dev: http://10.0.0.10:8001.
window.SOL_API_BASE = `${window.location.protocol}//${window.location.hostname}:8001`;

window.SOL_DATA = { DOMAINS, BOOKS, SAMPLE_TOC, SAMPLE_PAGE, DAILY };
