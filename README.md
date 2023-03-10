Помощник объединения модифицированных конфигураций. Помогает автоматически объединять те модули, которые не содержат признаков доработки, и запускает PMerge для тх модулей, где доработки есть.

Подддерживает как трехсторонее, так и двухстороннее объединение.

Суть работы:
Предполагается, что все доработки оформлены комментариями с отметкой разработчика.
Программа анализирует, есть ли в одном из входящих файлов такие комментарии, и если нет - просто использует режим "взять из файла".
Если есть - запускается PMerge с возможностью выбрать, какие изменения нужны.

Таким образом большинство модулей объединяется автоматически, а там, где нужен ручной контроль - он остается в полной мере.

Попутно пишется лог, где можно посмотреть, какие решения были приняты программой (путь к логу указывается в коммандной строке).

Настройка:

Зайти в конфигуратор -> Сервис -> Параметры -> Сравнение/объединение -> Добавить 

Объединение двух файлов:
-keywords "//#,//+" -exe .\P4Merge\p4merge.exe -log .\diff1c.log -tbase %baseCfgTitle -tnew %secondCfgTitle -base %baseCfg -new %secondCfg -merge %merged

Трехстороннее объединение:
-keywords "//#,//+" -exe .\P4Merge\p4merge.exe -log .\diff1c.log -tbase %baseCfgTitle -tnew %secondCfgTitle -told %oldVendorCfgTitle -old %oldVendorCfg -base %baseCfg -new %secondCfg -merge %merged

В приведенных примерах выше программа ищет комментарии //# и //+, лог пишет в diff1c.log в папке программы, PMerge расположен в подпапке .\P4Merge
Естественно, текущему пользователю должна быть доступна запись в каталог расположения лог-файла.

P4Merge можно скачать тут
https://www.perforce.com/downloads/visual-merge-tool

