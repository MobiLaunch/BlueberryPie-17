.pragma library

// Unit conversion. Linear units convert through a base unit; temperature is handled separately.
const CATEGORIES = [
    {id: "length", title: "Length", base: "m", units: {mm: 0.001, cm: 0.01, m: 1, km: 1000, in: 0.0254, ft: 0.3048, yd: 0.9144, mi: 1609.344}},
    {id: "mass", title: "Mass", base: "kg", units: {mg: 0.000001, g: 0.001, kg: 1, t: 1000, oz: 0.028349523125, lb: 0.45359237}},
    {id: "volume", title: "Volume", base: "l", units: {ml: 0.001, l: 1, tsp: 0.00492892159375, tbsp: 0.01478676478125, cup: 0.2365882365, gal: 3.785411784}},
    {id: "speed", title: "Speed", base: "m/s", units: {"m/s": 1, "km/h": 1 / 3.6, mph: 0.44704, kn: 0.514444444444}},
    {id: "data", title: "Data", base: "B", units: {B: 1, KB: 1000, MB: 1e6, GB: 1e9, TB: 1e12, KiB: 1024, MiB: 1048576, GiB: 1073741824}},
    {id: "temperature", title: "Temperature", base: "C", units: {"°C": 0, "°F": 0, K: 0}}
];

function category(id) {
    return CATEGORIES.find(item => item.id === id) || CATEGORIES[0];
}

function unitNames(id) {
    return Object.keys(category(id).units);
}

function toCelsius(value, unit) {
    return unit === "°F" ? (value - 32) * 5 / 9 : unit === "K" ? value - 273.15 : value;
}

function fromCelsius(value, unit) {
    return unit === "°F" ? value * 9 / 5 + 32 : unit === "K" ? value + 273.15 : value;
}

// Returns a number, or NaN when the input or units are not valid.
function convert(id, value, from, to) {
    const group = category(id);
    const number = typeof value === "number" ? value : parseFloat(String(value).replace(",", "."));
    const known = name => Object.prototype.hasOwnProperty.call(group.units, name);
    if (!isFinite(number) || !known(from) || !known(to))
        return NaN;
    if (group.id === "temperature") {
        const celsius = toCelsius(number, from);
        if (from === "K" && number < 0 || celsius < -273.15 - 1e-9)
            return NaN;
        return fromCelsius(celsius, to);
    }
    return number * group.units[from] / group.units[to];
}

function format(value) {
    if (!isFinite(value))
        return "";
    if (value === 0)
        return "0";
    const magnitude = Math.abs(value);
    if (magnitude >= 1e12 || magnitude < 1e-6)
        return value.toExponential(4).replace(/\.?0+e/, "e").replace("e+", "e");
    return String(parseFloat(value.toPrecision(8)));
}
