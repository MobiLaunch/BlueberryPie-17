.pragma library

// A small calculator language. It is parsed by hand (recursive descent); no text is
// ever passed to eval or Function.
//   numbers, + - * / × ÷ − ^ %, parentheses, unary minus, !, constants pi/π/e/ans,
//   functions sqrt cbrt abs ln log exp sin cos tan asin acos atan floor ceil round.

const FUNCTIONS = {
    sqrt: Math.sqrt, cbrt: Math.cbrt, abs: Math.abs, ln: Math.log, log: Math.log10, exp: Math.exp,
    floor: Math.floor, ceil: Math.ceil, round: Math.round
};
const TRIG = ["sin", "cos", "tan", "asin", "acos", "atan"];

function tokenize(text) {
    const tokens = [];
    const source = String(text).replace(/×/g, "*").replace(/÷/g, "/").replace(/−/g, "-").replace(/π/g, "pi").replace(/√/g, "sqrt");
    let i = 0;
    while (i < source.length) {
        const ch = source[i];
        if (/\s/.test(ch)) {
            i++;
        } else if (/[0-9.]/.test(ch)) {
            const match = /^(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/.exec(source.slice(i));
            if (!match)
                throw new Error("Check the number");
            tokens.push({type: "num", value: parseFloat(match[0])});
            i += match[0].length;
        } else if (/[a-z]/i.test(ch)) {
            const match = /^[a-z]+/i.exec(source.slice(i));
            tokens.push({type: "name", value: match[0].toLowerCase()});
            i += match[0].length;
        } else if ("+-*/^%!(),".indexOf(ch) >= 0) {
            tokens.push({type: "op", value: ch});
            i++;
        } else {
            throw new Error("Unexpected \"" + ch + "\"");
        }
    }
    return tokens;
}

function factorial(n) {
    if (n < 0 || n !== Math.floor(n))
        throw new Error("Factorial needs a whole number");
    if (n > 170)
        throw new Error("Too large");
    let result = 1;
    for (let k = 2; k <= n; k++)
        result *= k;
    return result;
}

function evaluate(text, options) {
    const settings = options || {};
    const degrees = settings.degrees === true;
    const ans = typeof settings.ans === "number" ? settings.ans : 0;
    try {
        const tokens = tokenize(text);
        if (tokens.length === 0)
            return {ok: false, error: ""};
        let position = 0;
        const peek = () => tokens[position];
        const take = value => {
            const token = tokens[position];
            if (token && token.type === "op" && token.value === value) {
                position++;
                return true;
            }
            return false;
        };
        function expression() {
            let left = term();
            for (; ;) {
                if (take("+"))
                    left += term();
                else if (take("-"))
                    left -= term();
                else
                    return left;
            }
        }
        function term() {
            let left = unary();
            for (; ;) {
                if (take("*")) {
                    left *= unary();
                } else if (take("/")) {
                    const right = unary();
                    if (right === 0)
                        throw new Error("Can't divide by zero");
                    left /= right;
                } else {
                    const next = peek();
                    // Implicit multiplication: 2(3+4), 2pi, (1+2)(3+4)
                    if (next && (next.type === "num" || next.type === "name" || (next.type === "op" && next.value === "(")))
                        left *= unary();
                    else
                        return left;
                }
            }
        }
        function power() {
            const base = postfix();
            if (take("^"))
                return Math.pow(base, unary());
            return base;
        }
        function unary() {
            if (take("-"))
                return -unary();
            if (take("+"))
                return unary();
            return power();
        }
        function postfix() {
            let value = primary();
            for (; ;) {
                if (take("%"))
                    value /= 100;
                else if (take("!"))
                    value = factorial(value);
                else
                    return value;
            }
        }
        function primary() {
            const token = tokens[position];
            if (!token)
                throw new Error("Unfinished expression");
            if (token.type === "num") {
                position++;
                return token.value;
            }
            if (token.type === "op" && token.value === "(") {
                position++;
                const inner = expression();
                if (!take(")"))
                    throw new Error("Missing )");
                return inner;
            }
            if (token.type === "name") {
                position++;
                if (token.value === "pi")
                    return Math.PI;
                if (token.value === "e")
                    return Math.E;
                if (token.value === "ans")
                    return ans;
                const trig = TRIG.indexOf(token.value) >= 0;
                const fn = trig ? Math[token.value] : FUNCTIONS[token.value];
                if (!fn)
                    throw new Error("Unknown \"" + token.value + "\"");
                const grouped = take("(");
                const argument = grouped ? expression() : unary();
                if (grouped && !take(")"))
                    throw new Error("Missing )");
                if (trig && token.value.length === 3)
                    return fn(degrees ? argument * Math.PI / 180 : argument);
                if (trig)
                    return degrees ? fn(argument) * 180 / Math.PI : fn(argument);
                return fn(argument);
            }
            throw new Error("Unexpected \"" + token.value + "\"");
        }
        const value = expression();
        if (position < tokens.length)
            throw new Error("Unexpected \"" + tokens[position].value + "\"");
        if (!isFinite(value))
            return {ok: false, error: "Not a real number"};
        // Tame float noise such as 0.1 + 0.2 and sin(180°).
        const cleaned = Math.abs(value) < 1e-12 ? 0 : parseFloat(value.toPrecision(14));
        return {ok: true, value: cleaned};
    } catch (error) {
        return {ok: false, error: String(error.message || error)};
    }
}

function format(value) {
    if (value === 0)
        return "0";
    const magnitude = Math.abs(value);
    if (magnitude >= 1e15 || magnitude < 1e-9)
        return value.toExponential(8).replace(/\.?0+e/, "e").replace("e+", "e");
    return String(parseFloat(value.toPrecision(12)));
}
