# Applied Natural Language Processing — From Tokens to Agents

ODTÜ'de bilgisayar mühendisi olmayan mühendisler ve İstatistik öğrencilerine
verilen Applied NLP dersinin herkese açık, etkileşimli, canlı kitabı.
Her iki sürüm de tamamlandı: 39 bölüm ve 6 ek, hem İngilizce (`en/`) hem
Türkçe (`tr/`), aynı pipeline'dan yayınlanıyor.

**Stack:** [Quarto](https://quarto.org) book × 2 (EN + TR) → GitHub Actions →
GitHub Pages. İnteraktifler Observable JS (tarayıcıda çalışır, sunucu yok);
kod bölümleri Python + Jupyter engine + `freeze`.

## Yardımcı repolar

Aynı klasör düzenini izleyen iki repo; bir bölümün notebook'u ve sunumu, bölüm
dosyasıyla aynı adı taşır (`en/chapters/01-why-nlp-now`):

| repo | içerik | yayın |
|:--|:--|:--|
| [uygulamali-dogal-dil-isleme-notebooks](https://github.com/bbardakk/uygulamali-dogal-dil-isleme-notebooks) | bölüm başına Jupyter notebook'lar | — |
| [uygulamali-dogal-dil-isleme-slides](https://github.com/bbardakk/uygulamali-dogal-dil-isleme-slides) | bölüm başına ders sunumları (EN + TR) | <https://bbardakk.github.io/uygulamali-dogal-dil-isleme-slides/> |

Kitap `bbardakk/metu-applied-nlp` adresinden taşındı; eski adresler yeni sitedeki
aynı sayfaya yönlenir.

## Atıf

Kitaba atıf verecekseniz sürümü ve erişim tarihini belirtin — bu yaşayan bir
kitap. Hazır künyeler (BibTeX + APA), lisans ayrımı ve baskı bilgisi:

- İngilizce: <https://bbardakk.github.io/uygulamali-dogal-dil-isleme/en/cite.html>
- Türkçe: <https://bbardakk.github.io/uygulamali-dogal-dil-isleme/tr/cite.html>

Depo kökündeki `CITATION.cff`, GitHub'ın **Cite this repository** düğmesini
besler ve Zenodo sürüm meta verisinin kaynağıdır.

**Lisans:** metin [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
kod [MIT](https://opensource.org/licenses/MIT). Ayrıntı: `LICENSE`.

```
.
├── en/                      # İngilizce kitap (tam Quarto projesi)
│   ├── _quarto.yml          # bölüm listesi, tema, footer — ana kontrol dosyası
│   ├── index.qmd            # landing page / kapak (BPE-chip hero)
│   ├── cite.qmd             # künye: atıf, lisans, sürüm, yazar, colophon
│   ├── preface.qmd          # önsöz
│   ├── chapters/            # 39 bölüm / 7 part
│   ├── appendices/          # kurulum, matematik, sözlük, bitirme projesi,
│   │                        #   ders planı, Türkçe kaynaklar
│   │                        #   glossary.csv = sözlüğün tek doğruluk kaynağı
│   ├── theme/               # custom-light.scss / custom-dark.scss
│   └── _templates/          # chapter-template.qmd — yeni bölüm için kopyala
├── tr/                      # Türkçe kitap (aynı yapı, tam çeviri)
├── .github/workflows/
│   ├── publish.yml          # main push → render en + tr → Pages deploy
│   └── pr-check.yml         # PR → render kontrolü (deploy yok)
├── scripts/                 # build-glossary.py — CSV'den iki sürümün de
│                            #   sözlük tablolarını üretir; check-* betikleri
│                            #   `make check` tarafından koşulur
├── index.html               # kök yönlendirme → /en/
└── Makefile                 # preview / render / serve / glossary kısayolları
```

## 1) Lokal kurulum ve önizleme

```bash
# Quarto: https://quarto.org/docs/get-started/  (>= 1.10)
pip install -r requirements.txt      # sadece Python'lu bölümler için
make preview                          # EN canlı önizleme (kaydettikçe yenilenir)
make preview-tr                       # TR canlı önizleme
make render && make serve             # iki dili birleştirip localhost:4200'de gez
```

## 2) İçerik değiştirme (günlük iş akışı)

- **Metin düzenleme:** ilgili `.qmd` dosyasını aç, yaz, kaydet — önizleme
  anında yenilenir. Bölümlerdeki `<!-- TODO(draft): ... -->` blokları yazım
  planıdır; render'da görünmez.
- **Bölüm ekleme / silme / sıralama:** `en/_quarto.yml` içindeki `chapters:`
  listesi tek doğruluk kaynağıdır; dosya adındaki `NN-` numarası oradaki
  sıradan türetilir. Yeni bölüm için template'i `en/chapters/NN-isim.qmd`
  olarak kopyala — `NN` yerine boşta olan herhangi bir numara (90, 91, …)
  yeter, doğrusunu script atayacak. Listede istediğin yere ekle, sonra:

  ```bash
  python3 scripts/renumber-chapters.py --dry-run   # planı gör
  python3 scripts/renumber-chapters.py             # uygula
  ```

  Script dosyaları `git mv` ile yeniden adlandırır ve her iki dildeki tüm
  bağlantıları düzeltir — bağlantı metnine yazılmış `[17. bölümde](...)`
  gibi numaralar dahil. `@sec-` çapraz referanslarına dokunmaz; numara
  değil çapa oldukları için zaten kırılmazlar. `make check` numara ile
  sıra uyuşmazsa build'i düşürür.
- **Sözlüğe terim ekleme:** `en/appendices/glossary.csv`'yi düzenle (grup
  sırası korunur, grup içinde alfabetik), sonra `make glossary`.
  `en/appendices/c-glossary.qmd` ve `tr/appendices/c-sozluk.qmd` içindeki
  tablolar üretilmiştir — elle düzenleme. `notes` sütunu İngilizce sayfaya,
  `notes_tr` Türkçe sayfaya gidiyor; `make check` birini doldurup diğerini
  boş bırakmayı reddeder.
- **İmza stiller:** vurgu için `[önemli ifade]{.hl}` (fosforlu kalem
  efekti); interaktifleri `::: {.anlp-widget}` bloğu içine al.
- **Çapraz referans:** başlık çapasıyla `@sec-transformers`; kaynakça için
  `en/references.bib`'e ekle, metinde `[@vaswani2017attention]`.
- **Tema:** tüm renk/font kararları `en/theme/custom-light.scss` başındaki
  altı token'da. TR tarafı kopya kullanır — değiştirince
  `cp en/theme/*.scss tr/theme/` ile eşitle.

## 3) İnteraktifler (OJS)

Örnekler: `en/chapters/07-transformers.qmd` içinde attention-head explorer,
`en/chapters/18-decoding-structured-output.qmd` içinde temperature/top-k/top-p
sampling explorer. Desen: `viewof x =
Inputs.range(...)` girdileri → hesap hücresi → `Plot.plot(...)`. Tamamı
tarayıcıda çalışır; build sırasında Python gerekmez. Yeni widget için bu
bloklardan birini kopyalayıp veriyi değiştir.

## 4) Python'lu bölümler ve `freeze`

`execute: freeze: auto` açık: bir bölümü lokalde render ettiğinde sonuçlar
`en/_freeze/` altına yazılır ve **commit edilir**. CI notebook'ları yeniden
çalıştırmaz — publish hızlı ve deterministik kalır. Kod hücresini
değiştirdiğinde lokalde bir kez `quarto render en` çalıştırıp `_freeze/`
değişikliklerini commit etmen yeterli.

## 5) Yayınlama

Kurulum tamamlandı — repo [bbardakk/uygulamali-dogal-dil-isleme](https://github.com/bbardakk/uygulamali-dogal-dil-isleme),
Pages kaynağı **GitHub Actions**. `main`'e her push iki dili render edip
yayınlar:

| URL | İçerik |
|---|---|
| <https://bbardakk.github.io/uygulamali-dogal-dil-isleme/> | köke gelen `/en/`'e yönlenir |
| <https://bbardakk.github.io/uygulamali-dogal-dil-isleme/en/> | İngilizce sürüm |
| <https://bbardakk.github.io/uygulamali-dogal-dil-isleme/tr/> | Türkçe sürüm |

İki workflow var:

- `.github/workflows/publish.yml` — `main` push'unda sözlük kontrolü +
  render + Pages deploy.
- `.github/workflows/pr-check.yml` — pull request'te sözlüğün CSV'siyle
  eşitliğini doğrular, iki dili de render eder, deploy etmez. Kırık build
  main'e giremez.

Sözlük kontrolü iki workflow'da da var: PR'sız doğrudan `main`'e push
yapılsa bile bayat bir sözlük tablosu yayına gidemez.

**Custom domain:** Settings → Pages → Custom domain; `public/` köküne CNAME
workflow'da eklenebilir (assemble adımına `echo "alan.adi" > public/CNAME`).

## 6) Yorumlar (giscus)

Repo public olduktan sonra: Discussions'ı aç → giscus app'i kur →
[giscus.app](https://giscus.app)'ten `repo-id`/`category-id` al →
`en/_quarto.yml` içindeki hazır `comments:` bloğunun yorumunu kaldırıp
değerleri yapıştır. TR için aynısını `tr/_quarto.yml`'a kopyala.

## 7) Türkçe sürümü büyütme

1. Terim önce `en/appendices/glossary.csv`'de sabitlenir (tek doğruluk
   kaynağı) ve `make glossary` ile iki sürümün tabloları da üretilir, sonra
   çeviri yapılır. `scripts/tr-terms.sh en/chapters/NN-xxx.qmd`, o bölümde
   glossary'ye bağlı her terimin onaylı Türkçe karşılığını yazdırır.
2. `en/chapters/NN-xxx.qmd` → `tr/chapters/NN-yyy.qmd` olarak çevir ve
   `tr/_quarto.yml` `chapters:` listesine ekle. Dosya adı iki sürümde
   **farklı** olmalı; `renumber-chapters.py` çakışmayı reddeder.
3. `tr/index.qmd`'deki kısım kartlarına ve `tr/_quarto.yml`'a ekle.
4. `make check` — bağlantılar, çapalar, sözlük kullanımı, OJS hücreleri ve
   tema eşitliği tek komutta doğrulanır.
5. Sidebar'daki dil değiştirici (🌐) iki yönü de bağlıyor; kök `/`
   yönlendirmesi `index.html`'de.

## 8) Viral dağıtım disiplini (her bölüm yayını)

- Bölümün "hero" görselini/interaktifini tek başına paylaşılabilir tut —
  paylaşılan şey link'tir, kitap trafiği ondan gelir.
- `en/index.qmd` sonundaki **Updates** tablosuna satır ekle (changelog).
- Duyuru seti: X/LinkedIn kısa thread + Show HN + r/MachineLearning;
  başlıkta hedef kitleyi söyle ("for engineers who aren't CS majors").

## Lisans

Metin **CC BY 4.0**, kod **MIT** — ayrıntı `LICENSE` dosyasında.
