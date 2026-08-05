# Indonesia Bot — Localization Examples

## Demonstration: Localization vs. Literal Translation

These examples show how the Indonesia bot adapts content for the Indonesian market,
not just translates English scripts word-for-word.

---

### Example 1: Greeting & Introduction

**❌ Literal Translation:**
> "Selamat siang. Saya Budi dari TalentBridge. Anda melamar posisi Customer Support. Saya akan melakukan screening."

**✅ Localized Version:**
> "Selamat siang, Bapak/Ibu. Saya Budi dari TalentBridge Indonesia. Terima kasih sudah melamar untuk posisi Customer Support Specialist di kantor Jakarta kami. Saya ingin melakukan screening singkat — sekitar 15 sampai 20 menit saja. Apakah sekarang waktunya pas, atau mau dijadwalkan ulang?"

**Why:** Indonesian business culture values politeness and respecting someone's time. The literal version is too blunt. The localized version:
- Uses "Bapak/Ibu" (essential formal address in Indonesian)
- Thanks the candidate for applying
- Sets time expectations ("15 sampai 20 menit saja" — the word "saja" softens it)
- Offers rescheduling (shows respect for their time)

---

### Example 2: Asking About Salary

**❌ Literal Translation:**
> "Berapa gaji Anda sekarang? Berapa gaji yang Anda harapkan?"

**✅ Localized Version:**
> "Bapak/Ibu, kalau boleh tahu, range kompensasi yang Bapak/Ibu harapkan berapa ya? Untuk posisi ini, kami punya range antara Rp8 juta sampai Rp15 juta per bulan, tergantung pengalaman. Apakah range tersebut sesuai dengan ekspektasi?"

**Why:** In Indonesian culture, directly asking current salary feels intrusive. The localized version:
- Opens with "kalau boleh tahu" (softener — "if I may ask")
- Shares the company's range FIRST (shows transparency, Indonesian candidates appreciate this)
- Uses "Rp8 juta" format (standard Indonesian currency expression)
- Asks if the range aligns rather than demanding a number

---

### Example 3: Handling "I'm not sure I want to change jobs"

**❌ Literal Translation:**
> "Anda harus memutuskan sekarang. Apakah Anda ingin melanjutkan atau tidak?"

**✅ Localized Version:**
> "Wajar sekali, Bapak/Ibu. Pindah kerja memang keputusan besar. Ini baru tahap awal — belum ada komitmen apa-apa. Anggap saja ini kesempatan untuk saling mengenal dan melihat apakah cocok. Kalau nanti Bapak/Ibu merasa tertarik, baru kita lanjutkan ke tahap berikutnya. Bagaimana?"

**Why:** "Saya pikir-pikir dulu" (let me think about it) in Indonesian culture is not a rejection — it's a normal response. The localized version:
- Validates their hesitation ("Wajar sekali" — very natural/understandable)
- Removes pressure ("belum ada komitmen apa-apa")
- Reframes as mutual exploration ("saling mengenal")
- Ends with soft "Bagaimana?" (how about that?) instead of demanding a decision

---

### Example 4: Regional Dialect Handling — Javanese-Accented Candidate

**Candidate says (Javanese-influenced):**
> "Mas Budi, gini mas, saya itu kerjanya di Surabaya. Nggak bisa pindah ke Jakarta soalnya keluarga di sini semua. Tapi kalau remote ya nggak masalah to?"

**Bot responds (adapting to register):**
> "Oke, Mas, terima kasih infonya. Saya paham, keluarga memang penting. Untuk posisi ini, saya cek dulu ya apakah bisa full remote dari Surabaya. Kalau bisa, berarti nggak perlu pindah. Sebentar ya, Mas."

**Key observations:**
- Bot adapts to "Mas" (Javanese informal address) since candidate used it first
- Uses "nggak" instead of formal "tidak" to match register
- Acknowledges family concern naturally
- Stays in Indonesian (doesn't switch to English)

---

### Example 5: Code-Switching — Finance/Tech English Terms in Bahasa

**Candidate says:**
> "Pengalaman saya mostly di backend development. Stack yang saya pakai Python sama Go, deploy pakai Kubernetes di AWS. Expected salary saya sekitar 20 juta per bulan."

**Bot responds:**
> "Bagus, Bapak. Pengalaman backend development dengan Python dan Go sangat relevan dengan posisi ini. Tim engineering kami juga pakai Kubernetes di AWS, jadi akan familiar. Untuk expected salary 20 juta per bulan, itu masih dalam range kami. Bisa cerita lebih detail tentang project terbesar yang pernah Bapak handle?"

**Key observations:**
- Tech terms kept in English (backend, Python, Go, Kubernetes, AWS) — natural in Indonesian tech conversations
- "Expected salary" understood and repeated naturally
- "Project" and "handle" are common loanwords in Indonesian professional context
- Bot doesn't try to translate tech terms to forced Indonesian equivalents

---

## Terminology Map

| English Term | Indonesian Equivalent | Notes |
|---|---|---|
| Interview | Interview / Wawancara | Both used, "interview" more common |
| Resume/CV | CV | Universally understood |
| Salary | Gaji / Kompensasi | "Gaji" = informal, "Kompensasi" = formal |
| Benefits | Benefit / Tunjangan | "Tunjangan" is the Indonesian word |
| Notice period | Notice period | No common Indonesian equivalent |
| Full-time | Full-time | Kept in English |
| Remote | Remote / WFH / Kerja dari rumah | All understood |
| Deadline | Deadline / Batas waktu | Both used |
| Team | Tim | Direct adoption |
| Manager | Manajer / Manager | Both acceptable |
| Experience | Pengalaman | Use Indonesian |
| Skills | Skill / Keahlian | Both common |
| Probation | Probation / Masa percobaan | "Masa percobaan" is formal |
| Backend/Frontend | Backend/Frontend | Never translated |

## Currency & Number Formatting
- Use "Rp" prefix: Rp8.000.000 or "8 juta"
- Indonesian uses period for thousands: 15.000.000
- Colloquial: "8 juta", "15 juta" (drop the zeros)
- Formal: "Rp8.000.000 per bulan"
