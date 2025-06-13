// Code.gs (캐싱 기능이 추가된 최종 버전)

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('웹툰 관리자')
    .addItem('앱 실행', 'showWebApp')
    .addToUi();
}

function showWebApp() {
  const html = HtmlService.createHtmlOutputFromFile('index')
    .setWidth(1000)
    .setHeight(800);
  SpreadsheetApp.getUi().showModalDialog(html, '웹툰 관리자');
}

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('웹툰 관리자')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * 웹툰 데이터를 시트에서 읽어오거나, 캐시에서 빠르게 가져옵니다.
 */
function getWebtoonData() {
  // 스크립트 캐시를 사용합니다.
  const cache = CacheService.getScriptCache();
  const CACHE_KEY = 'webtoon_data';

  // 1. 캐시에 저장된 데이터가 있는지 확인
  const cachedData = cache.get(CACHE_KEY);
  if (cachedData != null) {
    console.log('캐시에서 데이터를 성공적으로 불러왔습니다.');
    return JSON.parse(cachedData);
  }

  console.log('캐시에 데이터가 없어 시트에서 직접 읽어옵니다. (이 작업은 몇 분 걸릴 수 있습니다)');
  
  // 2. 캐시에 데이터가 없으면 시트에서 직접 읽어옵니다.
  try {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = spreadsheet.getSheetByName('Webtoons'); // 시트 이름 확인!
    if (!sheet) {
      throw new Error("시트 'Webtoons'을 찾을 수 없습니다.");
    }

    const range = sheet.getDataRange();
    const values = range.getValues();
    
    if (values.length < 2) return []; // 데이터가 없으면 빈 배열 반환

    const headers = values.shift();
    
    const result = values.map(function(row, index) {
      const webtoon = {};
      headers.forEach(function(header, colIndex) {
        if (header === 'episodes' || header === 'id') {
          webtoon[header] = Number(row[colIndex]) || 0;
        } else {
          webtoon[header] = row[colIndex] || '';
        }
      });
      return webtoon;
    });

    // 3. 시트에서 읽어온 데이터를 다음 사용을 위해 캐시에 저장합니다.
    // 300초 = 5분. 이 시간 동안은 시트를 다시 읽지 않습니다.
    cache.put(CACHE_KEY, JSON.stringify(result), 300); 
    console.log('새로운 데이터를 캐시에 저장했습니다.');
    
    return result;

  } catch (e) {
    console.error("데이터 로드 중 심각한 오류 발생:", e);
    // 오류가 발생했을 때 빈 배열을 반환하여 무한 로딩을 방지
    return []; 
  }
}


/**
 * ID를 기반으로 시트에서 특정 행들을 삭제합니다.
 */
function deleteRowsByIds(idsToDelete) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Webtoons');
    if (!sheet) return "시트를 찾을 수 없습니다.";

    const idsSet = new Set(idsToDelete.map(String));
    const data = sheet.getDataRange().getValues();
    const idColumnIndex = data[0].indexOf('id');

    if (idColumnIndex === -1) return "'id' 열을 찾을 수 없습니다.";

    for (let i = data.length - 1; i >= 1; i--) {
      const currentId = String(data[i][idColumnIndex]);
      if (idsSet.has(currentId)) {
        sheet.deleteRow(i + 1);
      }
    }
    
    // 중요: 데이터가 변경되었으므로 캐시를 삭제합니다.
    CacheService.getScriptCache().remove('webtoon_data');
    console.log('데이터 삭제 후 캐시를 비웠습니다.');

    return "선택된 항목이 삭제되었습니다.";
  } catch(e) {
    console.error("삭제 작업 실패:", e);
    return "오류가 발생하여 삭제하지 못했습니다.";
  }
}