"use client";

import {
  BookOpen,
  CheckCircle2,
  FilePlus2,
  Globe2,
  LockKeyhole,
  RefreshCcw,
  Search,
  Trash2,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  WorkspaceRequired,
} from "@/components/workspace/workspace-required";

import {
  useWorkspace,
} from "@/contexts/workspace-context";

import {
  employeesService,
  type Employee,
} from "@/services/employees.service";

import {
  knowledgeService,
} from "@/services/knowledge.service";

import type {
  KnowledgeCategory,
  KnowledgePublic,
  KnowledgeStatus,
  KnowledgeVisibility,
} from "@/types/knowledge";


type ViewMode =
  | "mine"
  | "workspace";


export default function KnowledgePage() {
  return (
    <WorkspaceRequired>
      <KnowledgeContent />
    </WorkspaceRequired>
  );
}


function KnowledgeContent() {
  const {
    workspaceId,
    workspace,
    user,
  } =
    useWorkspace();


  const [
    employee,
    setEmployee,
  ] =
    useState<Employee | null>(
      null,
    );


  const [
    items,
    setItems,
  ] =
    useState<KnowledgePublic[]>(
      [],
    );


  const [
    view,
    setView,
  ] =
    useState<ViewMode>(
      "mine",
    );


  const [
    selectedId,
    setSelectedId,
  ] =
    useState<string | null>(
      null,
    );


  const [
    search,
    setSearch,
  ] =
    useState(
      "",
    );


  const [
    includeArchived,
    setIncludeArchived,
  ] =
    useState(
      false,
    );


  const [
    title,
    setTitle,
  ] =
    useState(
      "",
    );


  const [
    content,
    setContent,
  ] =
    useState(
      "",
    );


  const [
    category,
    setCategory,
  ] =
    useState<KnowledgeCategory>(
      "general",
    );


  const [
    status,
    setStatus,
  ] =
    useState<KnowledgeStatus>(
      "draft",
    );


  const [
    visibility,
    setVisibility,
  ] =
    useState<KnowledgeVisibility>(
      "private",
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const load =
    useCallback(
      async () => {
        if (
          !workspaceId ||
          !user?.id
        ) {
          setLoading(
            false,
          );

          return;
        }


        try {
          setLoading(
            true,
          );

          setError(
            null,
          );


          const employeesResponse =
            await employeesService.list(
              workspaceId,
              {
                includeInactive:
                  true,
              },
            );


          const currentEmployee =
            employeesResponse.employees.find(
              (
                item,
              ) =>
                item.user_id ===
                user.id,
            ) ??
            null;


          setEmployee(
            currentEmployee,
          );


          if (
            !currentEmployee
          ) {
            setItems(
              [],
            );

            return;
          }


          const response =
            view ===
            "mine"
              ? await knowledgeService.listMine(
                  workspaceId,
                  includeArchived,
                )
              : await knowledgeService.listWorkspace(
                  workspaceId,
                );


          setItems(
            response.items,
          );


          setSelectedId(
            (
              current,
            ) =>
              current &&
              response.items.some(
                (
                  item,
                ) =>
                  item.id ===
                  current,
              )
                ? current
                : response.items[0]?.id ??
                  null,
          );

        } catch (
          cause
        ) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Unable to load knowledge.",
          );

        } finally {
          setLoading(
            false,
          );
        }
      },
      [
        workspaceId,
        user?.id,
        view,
        includeArchived,
      ],
    );


  useEffect(
    () => {
      void load();
    },
    [
      load,
    ],
  );


  const selected =
    useMemo(
      () =>
        items.find(
          (
            item,
          ) =>
            item.id ===
            selectedId,
        ) ??
        null,
      [
        items,
        selectedId,
      ],
    );


  useEffect(
    () => {
      if (
        !selected
      ) {
        return;
      }


      setTitle(
        selected.title,
      );

      setContent(
        selected.content,
      );

      setCategory(
        selected.category,
      );

      setStatus(
        selected.status,
      );

      setVisibility(
        selected.visibility,
      );
    },
    [
      selected,
    ],
  );


  const filtered =
    useMemo(
      () => {
        const query =
          search
            .trim()
            .toLowerCase();


        if (
          !query
        ) {
          return items;
        }


        return items.filter(
          (
            item,
          ) =>
            `${item.title} ${item.content} ${item.category}`
              .toLowerCase()
              .includes(
                query,
              ),
        );
      },
      [
        items,
        search,
      ],
    );


  async function createEntry() {
    if (
      !workspaceId ||
      !employee
    ) {
      return;
    }


    try {
      setSaving(
        true,
      );


      const created =
        await knowledgeService.createMine(
          workspaceId,
          {
            owner_employee_id:
              employee.id,

            title:
              "Untitled Knowledge",

            content:
              "",

            category:
              "general",

            visibility:
              "private",
          },
        );


      setView(
        "mine",
      );


      setItems(
        (
          current,
        ) => [
          created,
          ...current,
        ],
      );


      setSelectedId(
        created.id,
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to create knowledge entry.",
      );

    } finally {
      setSaving(
        false,
      );
    }
  }


  async function saveEntry() {
    if (
      !workspaceId ||
      !selected ||
      view !==
      "mine" ||
      !title.trim()
    ) {
      return;
    }


    try {
      setSaving(
        true,
      );


      const updated =
        await knowledgeService.updateMine(
          workspaceId,
          selected.id,
          {
            title:
              title.trim(),

            content,

            category,

            status,

            visibility,
          },
        );


      setItems(
        (
          current,
        ) =>
          current.map(
            (
              item,
            ) =>
              item.id ===
              updated.id
                ? updated
                : item,
          ),
      );

    } catch (
      cause
    ) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to save knowledge entry.",
      );

    } finally {
      setSaving(
        false,
      );
    }
  }


  async function removeEntry() {
    if (
      !workspaceId ||
      !selected ||
      view !==
      "mine"
    ) {
      return;
    }


    if (
      !window.confirm(
        `Delete "${selected.title}"?`,
      )
    ) {
      return;
    }


    await knowledgeService.deleteMine(
      workspaceId,
      selected.id,
    );


    setItems(
      (
        current,
      ) =>
        current.filter(
          (
            item,
          ) =>
            item.id !==
            selected.id,
        ),
    );


    setSelectedId(
      null,
    );
  }


  return (
    <div
      style={{
        display:
          "grid",

        gap:
          14,
      }}
    >
      <header
        style={{
          display:
            "flex",

          justifyContent:
            "space-between",

          gap:
            12,
        }}
      >
        <div>
          <h1>
            Knowledge
          </h1>

          <p
            className="text-label"
            style={{
              marginTop:
                4,
            }}
          >
            Private and workspace knowledge for{" "}
            {workspace?.name ??
              "this workspace"}.
          </p>
        </div>


        <div
          style={{
            display:
              "flex",

            gap:
              8,
          }}
        >
          <button
            className="button button--outline"
            onClick={() => {
              void load();
            }}
          >
            <RefreshCcw
              size={
                14
              }
            />

            Refresh
          </button>


          <button
            className="button button--primary"
            disabled={
              !employee ||
              saving
            }
            onClick={() => {
              void createEntry();
            }}
          >
            <FilePlus2
              size={
                14
              }
            />

            New Knowledge
          </button>
        </div>
      </header>


      {error ? (
        <div
          className="auth-error"
        >
          {error}
        </div>
      ) : null}


      <section
        className="panel"
      >
        <div
          style={{
            display:
              "flex",

            gap:
              6,

            padding:
              10,

            borderBottom:
              "1px solid var(--color-border)",
          }}
        >
          <button
            className={
              view ===
              "mine"
                ? "button button--primary"
                : "button button--outline"
            }
            onClick={() =>
              setView(
                "mine",
              )
            }
          >
            <LockKeyhole
              size={
                13
              }
            />

            My Knowledge
          </button>


          <button
            className={
              view ===
              "workspace"
                ? "button button--primary"
                : "button button--outline"
            }
            onClick={() =>
              setView(
                "workspace",
              )
            }
          >
            <Globe2
              size={
                13
              }
            />

            Workspace Knowledge
          </button>
        </div>


        <div
          style={{
            display:
              "grid",

            gridTemplateColumns:
              "300px minmax(0, 1fr)",

            minHeight:
              620,
          }}
        >
          <aside
            style={{
              borderRight:
                "1px solid var(--color-border)",
            }}
          >
            <div
              style={{
                display:
                  "grid",

                gap:
                  8,

                padding:
                  10,

                borderBottom:
                  "1px solid var(--color-border)",
              }}
            >
              <div
                style={{
                  position:
                    "relative",
                }}
              >
                <Search
                  size={
                    14
                  }
                  style={{
                    position:
                      "absolute",

                    left:
                      10,

                    top:
                      10,

                    color:
                      "#85878a",
                  }}
                />

                <input
                  value={
                    search
                  }
                  placeholder="Search knowledge"
                  onChange={(
                    event,
                  ) =>
                    setSearch(
                      event.target.value,
                    )
                  }
                  style={{
                    ...inputStyle,

                    paddingLeft:
                      32,
                  }}
                />
              </div>


              {view ===
              "mine" ? (
                <label
                  style={{
                    display:
                      "flex",

                    alignItems:
                      "center",

                    gap:
                      6,

                    fontSize:
                      8,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={
                      includeArchived
                    }
                    onChange={(
                      event,
                    ) =>
                      setIncludeArchived(
                        event.target.checked,
                      )
                    }
                  />

                  Include archived
                </label>
              ) : null}
            </div>


            <div
              style={{
                maxHeight:
                  550,

                overflow:
                  "auto",
              }}
            >
              {filtered.map(
                (
                  item,
                ) => (
                  <button
                    key={
                      item.id
                    }
                    type="button"
                    onClick={() =>
                      setSelectedId(
                        item.id,
                      )
                    }
                    style={{
                      width:
                        "100%",

                      padding:
                        12,

                      border:
                        0,

                      borderBottom:
                        "1px solid #eeeae2",

                      background:
                        item.id ===
                        selectedId
                          ? "#faf5e7"
                          : "transparent",

                      textAlign:
                        "left",

                      cursor:
                        "pointer",
                    }}
                  >
                    <strong
                      style={{
                        fontSize:
                          9,
                      }}
                    >
                      {item.title}
                    </strong>


                    <div
                      className="text-label"
                      style={{
                        marginTop:
                          4,

                        fontSize:
                          7,

                        textTransform:
                          "capitalize",
                      }}
                    >
                      {item.category}
                      {" · "}
                      {item.status}
                      {" · "}
                      {item.visibility}
                    </div>
                  </button>
                ),
              )}
            </div>
          </aside>


          <main>
            {loading ? (
              <div
                className="skeleton"
                style={{
                  height:
                    560,

                  margin:
                    14,
                }}
              />
            ) : selected ? (
              <>
                <div
                  style={{
                    display:
                      "flex",

                    justifyContent:
                      "space-between",

                    gap:
                      8,

                    padding:
                      10,

                    borderBottom:
                      "1px solid var(--color-border)",
                  }}
                >
                  <div
                    style={{
                      display:
                        "flex",

                      alignItems:
                        "center",

                      gap:
                        7,
                    }}
                  >
                    <BookOpen
                      size={
                        14
                      }
                    />

                    <strong>
                      {view ===
                      "mine"
                        ? "Knowledge Editor"
                        : "Workspace Article"}
                    </strong>
                  </div>


                  {view ===
                  "mine" ? (
                    <button
                      className="button button--outline"
                      style={{
                        color:
                          "#b22d2d",
                      }}
                      onClick={() => {
                        void removeEntry();
                      }}
                    >
                      <Trash2
                        size={
                          13
                        }
                      />

                      Delete
                    </button>
                  ) : null}
                </div>


                <div
                  style={{
                    display:
                      "grid",

                    gap:
                      12,

                    padding:
                      16,
                  }}
                >
                  <input
                    value={
                      title
                    }
                    readOnly={
                      view ===
                      "workspace"
                    }
                    onChange={(
                      event,
                    ) =>
                      setTitle(
                        event.target.value,
                      )
                    }
                    style={{
                      ...inputStyle,

                      height:
                        44,

                      fontSize:
                        18,

                      fontWeight:
                        700,
                    }}
                  />


                  {view ===
                  "mine" ? (
                    <div
                      style={{
                        display:
                          "grid",

                        gridTemplateColumns:
                          "1fr 1fr 1fr",

                        gap:
                          8,
                      }}
                    >
                      <select
                        value={
                          category
                        }
                        onChange={(
                          event,
                        ) =>
                          setCategory(
                            event.target.value as
                              KnowledgeCategory,
                          )
                        }
                        style={inputStyle}
                      >
                        <option value="general">
                          General
                        </option>

                        <option value="process">
                          Process
                        </option>

                        <option value="reference">
                          Reference
                        </option>

                        <option value="learning">
                          Learning
                        </option>
                      </select>


                      <select
                        value={
                          status
                        }
                        onChange={(
                          event,
                        ) =>
                          setStatus(
                            event.target.value as
                              KnowledgeStatus,
                          )
                        }
                        style={inputStyle}
                      >
                        <option value="draft">
                          Draft
                        </option>

                        <option value="published">
                          Published
                        </option>

                        <option value="archived">
                          Archived
                        </option>
                      </select>


                      <select
                        value={
                          visibility
                        }
                        onChange={(
                          event,
                        ) =>
                          setVisibility(
                            event.target.value as
                              KnowledgeVisibility,
                          )
                        }
                        style={inputStyle}
                      >
                        <option value="private">
                          Private
                        </option>

                        <option value="workspace">
                          Workspace
                        </option>
                      </select>
                    </div>
                  ) : null}


                  <textarea
                    value={
                      content
                    }
                    readOnly={
                      view ===
                      "workspace"
                    }
                    maxLength={
                      200000
                    }
                    onChange={(
                      event,
                    ) =>
                      setContent(
                        event.target.value,
                      )
                    }
                    style={{
                      minHeight:
                        390,

                      padding:
                        12,

                      border:
                        "1px solid var(--color-border)",

                      borderRadius:
                        7,

                      outline:
                        "none",

                      resize:
                        "vertical",

                      background:
                        "#fffefa",

                      fontFamily:
                        "inherit",

                      fontSize:
                        10,

                      lineHeight:
                        1.65,
                    }}
                  />


                  {view ===
                  "mine" ? (
                    <div
                      style={{
                        display:
                          "flex",

                        justifyContent:
                          "flex-end",
                      }}
                    >
                      <button
                        className="button button--primary"
                        disabled={
                          saving ||
                          !title.trim()
                        }
                        onClick={() => {
                          void saveEntry();
                        }}
                      >
                        <CheckCircle2
                          size={
                            13
                          }
                        />

                        {saving
                          ? "Saving..."
                          : "Save Knowledge"}
                      </button>
                    </div>
                  ) : null}
                </div>
              </>
            ) : (
              <div
                style={{
                  minHeight:
                    560,

                  display:
                    "grid",

                  placeItems:
                    "center",

                  color:
                    "#777a7c",

                  fontSize:
                    10,
                }}
              >
                Select an entry.
              </div>
            )}
          </main>
        </div>
      </section>
    </div>
  );
}


const inputStyle = {
  width:
    "100%",

  height:
    36,

  padding:
    "0 10px",

  border:
    "1px solid var(--color-border)",

  borderRadius:
    7,

  outline:
    "none",

  background:
    "#fffefa",

  color:
    "#303235",

  fontSize:
    10,
} as const;