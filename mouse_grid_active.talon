tag: user.mouse_grid_active
-
key(`):           user.mouse_grid_exit()
# Failsafe - if the user is confused and just wants out, they'll probably hit
# `esc`, even though grave is more convenient (for ISO UK Qwerty - tilde on US?).
key(escape):      user.mouse_grid_exit()
key(tab):         user.mouse_grid_move()

# HACK: allow modifier clicks by explicitly binding them.
#
# Left Click
key(space):       user.mouse_grid_click(0)
key(ctrl-space):  user.mouse_grid_click(0, "ctrl")
key(shift-space): user.mouse_grid_click(0, "shift")
key(alt-space):   user.mouse_grid_click(0, "alt")
# Right Click
key(,):           user.mouse_grid_click(1)
key(ctrl-,):      user.mouse_grid_click(1, "ctrl")
key(shift-,):     user.mouse_grid_click(1, "shift")
key(alt-,):       user.mouse_grid_click(1, "alt")
# Middle Click
key(.):           user.mouse_grid_click(2)
key(ctrl-.):      user.mouse_grid_click(2, "ctrl")
key(shift-.):     user.mouse_grid_click(2, "shift")
key(alt-.):       user.mouse_grid_click(2, "alt")
# Drag - only allow left click drag for now.
key(/):           user.mouse_grid_click(0, "", true)
key(ctrl-/):      user.mouse_grid_click(0, "ctrl", true)
key(shift-/):     user.mouse_grid_click(0, "shift", true)
key(alt-/):       user.mouse_grid_click(0, "alt", true)

# Narrowing keys (letters) are bound explicitly
#
# TODO: Better way to bind letter keys? The list is {user.letter}.
key(a): user.mouse_grid_narrow("a")
key(b): user.mouse_grid_narrow("b")
key(c): user.mouse_grid_narrow("c")
key(d): user.mouse_grid_narrow("d")
key(e): user.mouse_grid_narrow("e")
key(f): user.mouse_grid_narrow("f")
key(g): user.mouse_grid_narrow("g")
key(h): user.mouse_grid_narrow("h")
key(i): user.mouse_grid_narrow("i")
key(j): user.mouse_grid_narrow("j")
key(k): user.mouse_grid_narrow("k")
key(l): user.mouse_grid_narrow("l")
key(m): user.mouse_grid_narrow("m")
key(n): user.mouse_grid_narrow("n")
key(o): user.mouse_grid_narrow("o")
key(p): user.mouse_grid_narrow("p")
key(q): user.mouse_grid_narrow("q")
key(r): user.mouse_grid_narrow("r")
key(s): user.mouse_grid_narrow("s")
key(t): user.mouse_grid_narrow("t")
key(u): user.mouse_grid_narrow("u")
key(v): user.mouse_grid_narrow("v")
key(w): user.mouse_grid_narrow("w")
key(x): user.mouse_grid_narrow("x")
key(y): user.mouse_grid_narrow("y")
key(z): user.mouse_grid_narrow("z")

# Cover the letters being capsed, shifted, mistyped upper, etc.
key(A): user.mouse_grid_narrow("a")
key(B): user.mouse_grid_narrow("b")
key(C): user.mouse_grid_narrow("c")
key(D): user.mouse_grid_narrow("d")
key(E): user.mouse_grid_narrow("e")
key(F): user.mouse_grid_narrow("f")
key(G): user.mouse_grid_narrow("g")
key(H): user.mouse_grid_narrow("h")
key(I): user.mouse_grid_narrow("i")
key(J): user.mouse_grid_narrow("j")
key(K): user.mouse_grid_narrow("k")
key(L): user.mouse_grid_narrow("l")
key(M): user.mouse_grid_narrow("m")
key(N): user.mouse_grid_narrow("n")
key(O): user.mouse_grid_narrow("o")
key(P): user.mouse_grid_narrow("p")
key(Q): user.mouse_grid_narrow("q")
key(R): user.mouse_grid_narrow("r")
key(S): user.mouse_grid_narrow("s")
key(T): user.mouse_grid_narrow("t")
key(U): user.mouse_grid_narrow("u")
key(V): user.mouse_grid_narrow("v")
key(W): user.mouse_grid_narrow("w")
key(X): user.mouse_grid_narrow("x")
key(Y): user.mouse_grid_narrow("y")
key(Z): user.mouse_grid_narrow("z")

# TODO: Allow using number keys to navigate the 4grid
key(1): user.mouse_grid_narrow("1")
key(2): user.mouse_grid_narrow("2")
key(3): user.mouse_grid_narrow("3")
key(4): user.mouse_grid_narrow("4")
key(5): user.mouse_grid_narrow("5")
key(6): user.mouse_grid_narrow("6")
key(7): user.mouse_grid_narrow("7")
key(8): user.mouse_grid_narrow("8")
key(9): user.mouse_grid_narrow("9")
