/**
 * Excel 导出工具 (基于 exceljs)
 * 各列表页导出按钮统一调用
 * - 生成带标题行 + 表头 + 斑马纹 + 边框 + 冻结窗格 + 自动筛选的样式化表格
 */
import ExcelJS from 'exceljs'

export interface ExportColumn<T = any> {
  /** 表头 */
  title: string
  /** 数据字段名 */
  key: string
  /** 可选格式化函数 */
  formatter?: (row: T) => string | number
}

/** 主题色 */
const THEME = {
  main: 'FF1677FF',       // 主色 (标题)
  mainDark: 'FF0E5FD8',   // 深主色 (表头)
  border: 'FFD9D9D9',     // 边框
  rowAlt: 'FFF5F8FF',     // 斑马纹浅蓝
  white: 'FFFFFFFF',      // 白
  text: 'FF262626',       // 正文
}

/** 将数据导出为样式化的 Excel 文件 */
export async function exportToExcel<T = any>(
  columns: ExportColumn<T>[],
  rows: T[],
  fileName = '导出数据',
  sheetName = 'Sheet1',
  titleText?: string,
) {
  const colCount = columns.length

  const workbook = new ExcelJS.Workbook()
  workbook.creator = '智聘云图'
  workbook.created = new Date()

  const sheet = workbook.addWorksheet(sheetName.slice(0, 31), {
    views: [{ state: 'frozen', ySplit: 2 }],
  })

  // 标题行 (合并整行, 主题色底 + 白字)
  sheet.mergeCells(1, 1, 1, colCount)
  const titleRow = sheet.getRow(1)
  titleRow.height = 30
  const titleCell = titleRow.getCell(1)
  titleCell.value = titleText || fileName
  titleCell.alignment = { horizontal: 'center', vertical: 'middle' }
  titleCell.font = { name: '微软雅黑', size: 14, bold: true, color: { argb: THEME.white } }
  titleCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: THEME.main } }

  // 表头行
  const headerRow = sheet.getRow(2)
  headerRow.height = 24
  columns.forEach((c, i) => {
    const cell = headerRow.getCell(i + 1)
    cell.value = c.title
    cell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true }
    cell.font = { name: '微软雅黑', size: 11, bold: true, color: { argb: THEME.white } }
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: THEME.mainDark } }
    cell.border = {
      top: { style: 'thin', color: { argb: THEME.white } },
      bottom: { style: 'thin', color: { argb: THEME.white } },
      left: { style: 'thin', color: { argb: THEME.white } },
      right: { style: 'thin', color: { argb: THEME.white } },
    }
  })

  // 数据行 (斑马纹 + 边框 + 居中)
  rows.forEach((row, r) => {
    const excelRow = sheet.getRow(r + 3)
    excelRow.height = 22
    columns.forEach((c, i) => {
      const cell = excelRow.getCell(i + 1)
      cell.value = c.formatter ? c.formatter(row) : (row as any)[c.key] ?? ''
      cell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true }
      cell.font = { name: '微软雅黑', size: 11, color: { argb: THEME.text } }
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: r % 2 === 0 ? THEME.rowAlt : THEME.white },
      }
      cell.border = {
        top: { style: 'thin', color: { argb: THEME.border } },
        bottom: { style: 'thin', color: { argb: THEME.border } },
        left: { style: 'thin', color: { argb: THEME.border } },
        right: { style: 'thin', color: { argb: THEME.border } },
      }
    })
  })

  // 列宽
  columns.forEach((c, i) => {
    sheet.getColumn(i + 1).width = Math.max(c.title.length * 2 + 6, 14)
  })

  // 自动筛选 (表头行)
  if (rows.length > 0) {
    sheet.autoFilter = {
      from: { row: 2, column: 1 },
      to: { row: rows.length + 2, column: colCount },
    }
  }

  // 生成并下载
  const buffer = await workbook.xlsx.writeBuffer()
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${fileName}.xlsx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}