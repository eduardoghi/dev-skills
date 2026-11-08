---
name: qt-pitfalls
description: Mistakes in QML that compile, pass qmllint and fail only on screen. Use when writing or reviewing QML.
paths: "**/*.qml"
---

# QML pitfalls

These compile, pass qmllint and fail only when the screen is looked at, so check each change that
touches them on screen before calling it done.

## The JavaScript of QML is not a browser's

The QML engine lacks parts of recent JavaScript. `Object.fromEntries` is one of them. A binding
that calls a missing function throws, and QML keeps the old value or leaves the property empty,
so a button bound to it just stays off. Before using a newer built-in in QML, check it in a
`TestCase` run by `qmltestrunner`:

```qml
verify(typeof Object.fromEntries === "function")
```

`reduce`, `??`, `?.`, `padStart`, `includes` and `findIndex` work.

## A popup sized by the list inside it opens with no height

A `ListView` creates only the rows that fit its own height. When the popup takes its height from
the `contentHeight` of that list, both start at zero and stay there, and the popup opens empty.
Size it from the model instead:

```qml
height: Math.min(model.length * rowHeight + topPadding + bottomPadding, maxHeight)
```

## A transparent icon color doesn't hide the icon

`icon.color: "transparent"` means "don't tint", so the icon shows in the colors of the file. To
keep the space of an icon without showing one, as for the unchecked rows of a list, point
`icon.source` at an empty SVG of the same size.

## ComboBox with a plain list

- The `model` property doesn't give back the JavaScript array it was set to, so `model.indexOf`
  fails. Keep the array in a property of its own and use that.
- The text of the box has padding on both sides, about 40 px in a styled one. A box narrower than
  the padding, the indicator and the text shows only the indicator. Check the width with the
  longest entry.
